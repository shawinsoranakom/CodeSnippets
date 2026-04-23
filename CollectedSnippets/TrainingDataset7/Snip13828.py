def root_urlconf_changed(*, setting, **kwargs):
    if setting == "ROOT_URLCONF":
        from django.urls import clear_url_caches, set_urlconf

        clear_url_caches()
        set_urlconf(None)