def create_contenttypes(
    app_config,
    verbosity=2,
    interactive=True,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs,
):
    """
    Create content types for models in the given app.
    """
    if not app_config.models_module:
        return

    try:
        app_config = apps.get_app_config(app_config.label)
        ContentType = apps.get_model("contenttypes", "ContentType")
    except LookupError:
        return

    if not router.allow_migrate_model(using, ContentType):
        return

    all_model_names = {model._meta.model_name for model in app_config.get_models()}

    if not all_model_names:
        return

    ContentType.objects.clear_cache()

    existing_model_names = set(
        ContentType.objects.using(using)
        .filter(app_label=app_config.label)
        .values_list("model", flat=True)
    )

    cts = [
        ContentType(app_label=app_config.label, model=model_name)
        for model_name in sorted(all_model_names - existing_model_names)
    ]
    ContentType.objects.using(using).bulk_create(cts)
    if verbosity >= 2:
        for ct in cts:
            print(f"Adding content type '{ct.app_label} | {ct.model}'")