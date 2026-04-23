def storages_changed(*, setting, **kwargs):
    from django.contrib.staticfiles.storage import staticfiles_storage
    from django.core.files.storage import default_storage, storages

    if setting in (
        "STORAGES",
        "STATIC_ROOT",
        "STATIC_URL",
    ):
        try:
            del storages.backends
        except AttributeError:
            pass
        storages._backends = None
        storages._storages = {}

        default_storage._wrapped = empty
        staticfiles_storage._wrapped = empty