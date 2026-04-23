def check_csrf_cookie_secure(app_configs, **kwargs):
    passed_check = (
        settings.CSRF_USE_SESSIONS
        or not _csrf_middleware()
        or settings.CSRF_COOKIE_SECURE is True
    )
    return [] if passed_check else [W016]