def check_sts(app_configs, **kwargs):
    passed_check = not _security_middleware() or settings.SECURE_HSTS_SECONDS
    return [] if passed_check else [W004]