def patch_formats(lang, **settings):
    from django.utils.formats import _format_cache

    # Populate _format_cache with temporary values
    for key, value in settings.items():
        _format_cache[(key, lang)] = value
    try:
        yield
    finally:
        reset_format_cache()