from androguard.core.apk import APK

def analyze_apk(apk_path):
    """
    Reads an APK and extracts permissions.
    """

    app = APK(apk_path)

    permissions = app.get_permissions()

    package_name = app.get_package()

    app_name = app.get_app_name()

    return {
        "app_name": app_name,
        "package_name": package_name,
        "permissions": permissions
    }