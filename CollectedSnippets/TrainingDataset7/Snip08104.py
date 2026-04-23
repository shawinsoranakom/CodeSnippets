def check_storages(app_configs, **kwargs):
    """Ensure staticfiles is defined in STORAGES setting."""
    errors = []
    if STATICFILES_STORAGE_ALIAS not in settings.STORAGES:
        errors.append(E005)
    return errors