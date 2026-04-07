def check_allowed_hosts(app_configs, **kwargs):
    return [] if settings.ALLOWED_HOSTS else [W020]