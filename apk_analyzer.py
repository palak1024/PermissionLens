"""
apk_analyzer.py
================
PermissionLens — APK Analyzer module (Person 2's component).

Performs STATIC analysis only. Never installs or executes the APK.
Extracts:
  - App metadata (name, package, version, SDK info)
  - Declared permissions, categorized by sensitivity
  - Manifest details (components, exported activities, etc.)
  - Sensitive API "evidence" (references to camera, location, mic,
    contacts, SMS APIs found in the compiled bytecode)

Usage:
    python apk_analyzer.py path/to/app.apk
    python apk_analyzer.py path/to/app.apk --json report.json

Dependencies:
    pip install androguard
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List

from androguard.core.apk import APK
from androguard.core.analysis.analysis import Analysis
from androguard.misc import AnalyzeAPK


# ---------------------------------------------------------------------------
# Permission sensitivity knowledge base
# ---------------------------------------------------------------------------
# Maps a subset of the permission string to a sensitivity tier used by the
# risk engine later in the pipeline. Extend this table as needed.

PERMISSION_SENSITIVITY: Dict[str, str] = {
    "android.permission.INTERNET": "LOW",
    "android.permission.ACCESS_NETWORK_STATE": "LOW",
    "android.permission.CAMERA": "HIGH",
    "android.permission.RECORD_AUDIO": "HIGH",
    "android.permission.ACCESS_FINE_LOCATION": "HIGH",
    "android.permission.ACCESS_COARSE_LOCATION": "MEDIUM",
    "android.permission.READ_CONTACTS": "HIGH",
    "android.permission.WRITE_CONTACTS": "HIGH",
    "android.permission.READ_SMS": "HIGH",
    "android.permission.SEND_SMS": "HIGH",
    "android.permission.READ_CALL_LOG": "HIGH",
    "android.permission.READ_PHONE_STATE": "MEDIUM",
    "android.permission.READ_EXTERNAL_STORAGE": "MEDIUM",
    "android.permission.WRITE_EXTERNAL_STORAGE": "MEDIUM",
    "android.permission.BLUETOOTH": "LOW",
    "android.permission.POST_NOTIFICATIONS": "LOW",
}

DEFAULT_SENSITIVITY = "UNKNOWN"


# ---------------------------------------------------------------------------
# Sensitive API signatures to search for in the disassembled bytecode.
# Each entry maps a human-readable capability to a list of substrings that,
# if found in a method/class reference, count as "evidence" that capability
# is actually reachable in code (not just declared in the manifest).
# ---------------------------------------------------------------------------

SENSITIVE_API_SIGNATURES: Dict[str, List[str]] = {
    "Camera": [
        "Landroid/hardware/Camera;",
        "Landroid/hardware/camera2/CameraManager;",
        "Landroid/hardware/camera2/CameraDevice;",
    ],
    "Location": [
        "Landroid/location/LocationManager;",
        "Lcom/google/android/gms/location/FusedLocationProviderClient;",
    ],
    "Microphone": [
        "Landroid/media/MediaRecorder;",
        "Landroid/media/AudioRecord;",
    ],
    "Contacts": [
        "Landroid/provider/ContactsContract;",
    ],
    "SMS": [
        "Landroid/telephony/SmsManager;",
        "Landroid/provider/Telephony;",
    ],
    "Device Identifiers": [
        "Landroid/telephony/TelephonyManager;->getDeviceId",
        "Landroid/telephony/TelephonyManager;->getImei",
        "Landroid/telephony/TelephonyManager;->getSubscriberId",
    ],
    "Network / HTTP": [
        "Ljava/net/HttpURLConnection;",
        "Lokhttp3/OkHttpClient;",
        "Lorg/apache/http/client/HttpClient;",
    ],
    "Reflection (obfuscation indicator)": [
        "Ljava/lang/reflect/Method;->invoke",
        "Ljava/lang/Class;->forName",
    ],
    "Dynamic Code Loading": [
        "Ldalvik/system/DexClassLoader;",
        "Ldalvik/system/PathClassLoader;",
    ],
}


@dataclass
class PermissionFinding:
    permission: str
    sensitivity: str


@dataclass
class ApiEvidence:
    capability: str
    matched_signature: str
    class_or_method: str


@dataclass
class AnalysisReport:
    file_path: str
    app_name: str
    package_name: str
    version_name: str
    version_code: str
    min_sdk: str
    target_sdk: str
    compile_sdk: str
    is_debuggable: bool
    permissions: List[PermissionFinding] = field(default_factory=list)
    activities: List[str] = field(default_factory=list)
    exported_activities: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    receivers: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    api_evidence: List[ApiEvidence] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def classify_permission(perm: str) -> str:
    return PERMISSION_SENSITIVITY.get(perm, DEFAULT_SENSITIVITY)


def extract_manifest_info(apk: APK, report: AnalysisReport) -> None:
    """Populate component lists (activities, services, receivers, providers)."""
    report.activities = list(apk.get_activities())
    report.services = list(apk.get_services())
    report.receivers = list(apk.get_receivers())
    report.providers = list(apk.get_providers())

    exported = []
    for activity in report.activities:
        try:
            # get_intent_filters returns {} if none declared
            filters = apk.get_intent_filters("activity", activity)
            declared_exported = apk.get_element(
                "activity", "exported", name=activity
            )
            if declared_exported == "true" or (filters and declared_exported is None):
                exported.append(activity)
        except Exception:
            continue
    report.exported_activities = exported


def extract_permissions(apk: APK, report: AnalysisReport) -> None:
    for perm in apk.get_permissions():
        report.permissions.append(
            PermissionFinding(permission=perm, sensitivity=classify_permission(perm))
        )


def scan_sensitive_apis(analysis: Analysis, report: AnalysisReport) -> None:
    """
    Walk every class/method reference found by Androguard's analysis engine
    and flag any that match a known sensitive-API signature. This is the
    "API evidence" layer referenced in the PermissionLens synopsis — it
    distinguishes a declared-but-unused permission from one backed by an
    actual code path.
    """
    seen = set()

    for cls in analysis.get_classes():
        class_name = cls.name
        for method in cls.get_methods():
            method_analysis = method
            full_ref = f"{class_name}->{method_analysis.name}"

            for capability, signatures in SENSITIVE_API_SIGNATURES.items():
                for sig in signatures:
                    if sig in class_name or sig in full_ref:
                        key = (capability, sig, full_ref)
                        if key not in seen:
                            seen.add(key)
                            report.api_evidence.append(
                                ApiEvidence(
                                    capability=capability,
                                    matched_signature=sig,
                                    class_or_method=full_ref,
                                )
                            )

    # Also scan raw string pool / xref calls for cases the class walk misses
    # (e.g. calls made via reflection or from library code not tied to a
    # user-defined class we iterated above).
    try:
        for cls in analysis.get_external_classes():
            class_name = cls.name
            for capability, signatures in SENSITIVE_API_SIGNATURES.items():
                for sig in signatures:
                    if sig in class_name:
                        key = (capability, sig, class_name)
                        if key not in seen:
                            seen.add(key)
                            report.api_evidence.append(
                                ApiEvidence(
                                    capability=capability,
                                    matched_signature=sig,
                                    class_or_method=class_name,
                                )
                            )
    except Exception:
        pass


def analyze(apk_path: str) -> AnalysisReport:
    print(f"[*] Loading APK: {apk_path}")
    apk, dalvik_vm_format, analysis = AnalyzeAPK(apk_path)

    report = AnalysisReport(
        file_path=apk_path,
        app_name=str(apk.get_app_name() or "Unknown"),
        package_name=str(apk.get_package() or "Unknown"),
        version_name=str(apk.get_androidversion_name() or "Unknown"),
        version_code=str(apk.get_androidversion_code() or "Unknown"),
        min_sdk=str(apk.get_min_sdk_version() or "Unknown"),
        target_sdk=str(apk.get_target_sdk_version() or "Unknown"),
        compile_sdk=str(apk.get_effective_target_sdk_version() or "Unknown"),
        is_debuggable=bool(apk.get_attribute_value("application", "debuggable") == "true"),
    )

    print("[*] Extracting permissions...")
    extract_permissions(apk, report)

    print("[*] Extracting manifest / component details...")
    extract_manifest_info(apk, report)

    print("[*] Scanning bytecode for sensitive API evidence (this can take a while)...")
    scan_sensitive_apis(analysis, report)

    return report


def print_summary(report: AnalysisReport) -> None:
    print("\n" + "=" * 60)
    print("       PERMISSIONLENS — STATIC ANALYSIS REPORT")
    print("=" * 60)
    print(f"App Name:        {report.app_name}")
    print(f"Package:         {report.package_name}")
    print(f"Version:         {report.version_name} (code {report.version_code})")
    print(f"Min SDK:         {report.min_sdk}")
    print(f"Target SDK:      {report.target_sdk}")
    print(f"Debuggable:      {report.is_debuggable}")

    print("\n" + "-" * 60)
    print("PERMISSIONS")
    print("-" * 60)
    if not report.permissions:
        print("  (none declared)")
    for p in sorted(report.permissions, key=lambda x: x.sensitivity, reverse=True):
        marker = {"HIGH": "🔴", "MEDIUM": "⚠", "LOW": "✓", "UNKNOWN": "?"}.get(
            p.sensitivity, "?"
        )
        print(f"  {marker} {p.permission:<45} [{p.sensitivity}]")

    print("\n" + "-" * 60)
    print("COMPONENTS")
    print("-" * 60)
    print(f"  Activities:  {len(report.activities)}  (exported: {len(report.exported_activities)})")
    print(f"  Services:    {len(report.services)}")
    print(f"  Receivers:   {len(report.receivers)}")
    print(f"  Providers:   {len(report.providers)}")

    print("\n" + "-" * 60)
    print("SENSITIVE API EVIDENCE")
    print("-" * 60)
    if not report.api_evidence:
        print("  (no sensitive API references detected)")
    else:
        by_capability: Dict[str, int] = {}
        for e in report.api_evidence:
            by_capability[e.capability] = by_capability.get(e.capability, 0) + 1
        for capability, count in sorted(by_capability.items()):
            print(f"  ✓ {capability}: {count} reference(s) found")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="PermissionLens APK Analyzer — static permission & API evidence extractor"
    )
    parser.add_argument("apk_path", help="Path to the .apk file to analyze")
    parser.add_argument(
        "--json", dest="json_out", help="Optional path to write full results as JSON"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress the human-readable summary"
    )
    args = parser.parse_args()

    try:
        report = analyze(args.apk_path)
    except FileNotFoundError:
        print(f"[!] File not found: {args.apk_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Failed to analyze APK: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print_summary(report)

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        print(f"[*] Full JSON report written to: {args.json_out}")


if __name__ == "__main__":
    main()
