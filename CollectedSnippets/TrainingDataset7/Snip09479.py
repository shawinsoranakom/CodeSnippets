def complain(*args, **kwargs):
    raise ImproperlyConfigured(
        "settings.DATABASES is improperly configured. "
        "Please supply the ENGINE value. Check "
        "settings documentation for more details."
    )