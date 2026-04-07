def static_finders_changed(*, setting, **kwargs):
    if setting in {
        "STATICFILES_DIRS",
        "STATIC_ROOT",
    }:
        from django.contrib.staticfiles.finders import get_finder

        get_finder.cache_clear()