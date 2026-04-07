def check_default_cache_is_configured(app_configs, **kwargs):
    if DEFAULT_CACHE_ALIAS not in settings.CACHES:
        return [E001]
    return []