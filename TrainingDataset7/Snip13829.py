def static_storage_changed(*, setting, **kwargs):
    if setting in {
        "STATIC_ROOT",
        "STATIC_URL",
    }:
        from django.contrib.staticfiles.storage import staticfiles_storage

        staticfiles_storage._wrapped = empty