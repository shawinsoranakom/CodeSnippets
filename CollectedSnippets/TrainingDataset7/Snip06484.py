def inject_rename_contenttypes_operations(
    plan=None, apps=global_apps, using=DEFAULT_DB_ALIAS, **kwargs
):
    """
    Insert a `RenameContentType` operation after every planned `RenameModel`
    operation.
    """
    if plan is None:
        return

    # Determine whether or not the ContentType model is available.
    try:
        ContentType = apps.get_model("contenttypes", "ContentType")
    except LookupError:
        available = False
    else:
        if not router.allow_migrate_model(using, ContentType):
            return
        available = True

    for migration, backward in plan:
        if (migration.app_label, migration.name) == ("contenttypes", "0001_initial"):
            # There's no point in going forward if the initial contenttypes
            # migration is unapplied as the ContentType model will be
            # unavailable from this point.
            if backward:
                break
            else:
                available = True
                continue
        # The ContentType model is not available yet.
        if not available:
            continue
        inserts = []
        for index, operation in enumerate(migration.operations):
            if isinstance(operation, migrations.RenameModel):
                operation = RenameContentType(
                    migration.app_label,
                    operation.old_name_lower,
                    operation.new_name_lower,
                )
                inserts.append((index + 1, operation))
        for inserted, (index, operation) in enumerate(inserts):
            migration.operations.insert(inserted + index, operation)