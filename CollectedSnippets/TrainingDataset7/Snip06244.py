def _get_permission_metadata(apps, app_label, model_name):
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        # Model does not exist in this migration state, e.g. zero.
        Permission = apps.get_model("auth", "Permission")
        return Permission._meta.default_permissions, model_name
    return (
        model._meta.default_permissions,
        model._meta.verbose_name_raw,
    )