EXPECTED_PERMISSIONS = {
    "calculator": {"android.permission.INTERNET"},
    "camera": {
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.INTERNET",
    },
    "maps": {
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.INTERNET",
    },
    "messaging": {
        "android.permission.INTERNET",
        "android.permission.CAMERA",
        "android.permission.RECORD_AUDIO",
        "android.permission.READ_CONTACTS",
        "android.permission.POST_NOTIFICATIONS",
    },
    "photo_editor": {
        "android.permission.CAMERA",
        "android.permission.READ_MEDIA_IMAGES",
        "android.permission.INTERNET",
    },
}

PERMISSION_RISK = {
    "android.permission.INTERNET": 2,
    "android.permission.CAMERA": 7,
    "android.permission.RECORD_AUDIO": 10,
    "android.permission.ACCESS_FINE_LOCATION": 10,
    "android.permission.ACCESS_COARSE_LOCATION": 6,
    "android.permission.ACCESS_BACKGROUND_LOCATION": 15,
    "android.permission.READ_CONTACTS": 10,
    "android.permission.WRITE_CONTACTS": 10,
    "android.permission.READ_SMS": 15,
    "android.permission.RECEIVE_SMS": 12,
    "android.permission.SEND_SMS": 15,
    "android.permission.READ_CALL_LOG": 15,
    "android.permission.WRITE_CALL_LOG": 15,
    "android.permission.READ_PHONE_STATE": 8,
    "android.permission.READ_MEDIA_IMAGES": 6,
    "android.permission.READ_MEDIA_VIDEO": 6,
    "android.permission.POST_NOTIFICATIONS": 3,
}


def normalize_permission(permission):
    permission = permission.strip()
    if not permission:
        return permission
    if permission.startswith("android.permission."):
        return permission
    return f"android.permission.{permission}"


def get_severity(base_score, mismatch=False):
    score = base_score + (10 if mismatch else 0)
    if score >= 20:
        return "HIGH"
    if score >= 10:
        return "MEDIUM"
    return "LOW"


def get_risk_level(score):
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def calculate_risk(apk_data):
    """
    Input from Person 2 / Androguard:
    {
        "app_name": "...",
        "app_purpose": "calculator",
        "permissions": [...]
    }
    """
    app_name = apk_data.get("app_name", "Unknown application")
    purpose = str(apk_data.get("app_purpose", "")).lower().strip()
    permissions = [
        normalize_permission(p)
        for p in apk_data.get("permissions", [])
        if isinstance(p, str) and p.strip()
    ]

    expected = EXPECTED_PERMISSIONS.get(purpose, set())
    known_purpose = purpose in EXPECTED_PERMISSIONS

    score = 0
    findings = []

    for permission in permissions:
        base = PERMISSION_RISK.get(permission, 3)
        unusual = known_purpose and permission not in expected

        if unusual:
            score += base + 10
            findings.append({
                "permission": permission,
                "severity": get_severity(base, True),
                "type": "contextual_mismatch",
                "reason": (
                    f"{permission} is not normally expected for a "
                    f"{purpose} application."
                ),
            })
        else:
            score += base
            if base >= 7:
                findings.append({
                    "permission": permission,
                    "severity": get_severity(base),
                    "type": "sensitive_permission",
                    "reason": (
                        f"{permission} is a sensitive Android permission "
                        "and should be justified by the application's functionality."
                    ),
                })

    if "android.permission.ACCESS_BACKGROUND_LOCATION" in permissions:
        score += 5
        findings.append({
            "permission": "android.permission.ACCESS_BACKGROUND_LOCATION",
            "severity": "HIGH",
            "type": "contextual_mismatch",
            "reason": "Background location can allow location access beyond active app use.",
        })

    unique = []
    seen = set()
    for finding in findings:
        key = (finding["permission"], finding["type"])
        if key not in seen:
            seen.add(key)
            unique.append(finding)

    score = min(score, 100)

    return {
        "app_name": app_name,
        "app_purpose": purpose or None,
        "permissions_checked": permissions,
        "risk_score": score,
        "risk_level": get_risk_level(score),
        "findings": unique,
    }
