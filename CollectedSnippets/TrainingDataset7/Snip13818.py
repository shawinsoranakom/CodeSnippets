def clear_cache_handlers(*, setting, **kwargs):
    if setting == "CACHES":
        from django.core.cache import caches, close_caches

        close_caches()
        caches._settings = caches.settings = caches.configure_settings(None)
        caches._connections = Local()