def _i18n_cache_key_suffix(request, cache_key):
    """If necessary, add the current locale or time zone to the cache key."""
    if settings.USE_I18N:
        # first check if LocaleMiddleware or another middleware added
        # LANGUAGE_CODE to request, then fall back to the active language
        # which in turn can also fall back to settings.LANGUAGE_CODE
        cache_key += ".%s" % getattr(request, "LANGUAGE_CODE", get_language())
    if settings.USE_TZ:
        cache_key += ".%s" % get_current_timezone_name()
    return cache_key