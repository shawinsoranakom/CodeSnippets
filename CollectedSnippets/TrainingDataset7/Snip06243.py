def create_permissions(
    app_config,
    verbosity=2,
    interactive=True,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs,
):
    if not app_config.models_module:
        return

    try:
        Permission = apps.get_model("auth", "Permission")
    except LookupError:
        return
    if not router.allow_migrate_model(using, Permission):
        return

    # Ensure that contenttypes are created for this app. Needed if
    # 'django.contrib.auth' is in INSTALLED_APPS before
    # 'django.contrib.contenttypes'.
    create_contenttypes(
        app_config,
        verbosity=verbosity,
        interactive=interactive,
        using=using,
        apps=apps,
        **kwargs,
    )

    app_label = app_config.label
    try:
        app_config = apps.get_app_config(app_label)
        ContentType = apps.get_model("contenttypes", "ContentType")
    except LookupError:
        return

    models = list(app_config.get_models())

    # Grab all the ContentTypes.
    ctypes = ContentType.objects.db_manager(using).get_for_models(
        *models, for_concrete_models=False
    )

    # Find all the Permissions that have a content_type for a model we're
    # looking for. We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set(
        Permission.objects.using(using)
        .filter(
            content_type__in=set(ctypes.values()),
        )
        .values_list("content_type", "codename")
    )

    perms = []
    for model in models:
        ctype = ctypes[model]
        for codename, name in _get_all_permissions(model._meta):
            if (ctype.pk, codename) not in all_perms:
                permission = Permission()
                permission._state.db = using
                permission.codename = codename
                permission.name = name
                permission.content_type = ctype
                perms.append(permission)

    Permission.objects.using(using).bulk_create(perms)
    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '%s'" % perm)