def check_ssl_redirect(app_configs, **kwargs):
    passed_check = not _security_middleware() or settings.SECURE_SSL_REDIRECT is True
    return [] if passed_check else [W008]