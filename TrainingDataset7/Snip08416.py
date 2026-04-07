def check_url_settings(app_configs, **kwargs):
    errors = []
    for name in ("STATIC_URL", "MEDIA_URL"):
        value = getattr(settings, name)
        if value and not value.endswith("/"):
            errors.append(E006(name))
    return errors