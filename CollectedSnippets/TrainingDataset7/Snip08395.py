def check_csp_settings(app_configs, **kwargs):
    """
    Validate that CSP settings are properly configured when enabled.

    Ensures both SECURE_CSP and SECURE_CSP_REPORT_ONLY are dictionaries.
    """
    # CSP settings must be a dictionary or None.
    return [
        Error(E026.msg % (name, value), id=E026.id)
        for name in ("SECURE_CSP", "SECURE_CSP_REPORT_ONLY")
        if (value := getattr(settings, name, None)) is not None
        and not isinstance(value, dict)
    ]