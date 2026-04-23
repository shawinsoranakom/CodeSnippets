def check_url_config(app_configs, **kwargs):
    if getattr(settings, "ROOT_URLCONF", None):
        from django.urls import get_resolver

        resolver = get_resolver()
        return check_resolver(resolver)
    return []