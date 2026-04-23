def rename_permissions_after_model_rename(
    app_config,
    verbosity=2,
    plan=None,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    stdout=sys.stdout,
    **kwargs,
):
    if not app_config.models_module:
        return

    # This handler is connected to the global post_migrate signal, which is
    # emitted for *all* apps — including test configurations where
    # django.contrib.auth is NOT installed.
    try:
        Permission = apps.get_model("auth", "Permission")
    except LookupError:
        return
    if not router.allow_migrate_model(using, Permission):
        return

    db = using or router.db_for_write(Permission)

    app_label = app_config.label

    # Collect (from_model, to_model) pairs
    renames = [
        (op.new_name, op.old_name) if backward else (op.old_name, op.new_name)
        for migration, backward in (plan or [])
        for op in migration.operations
        if isinstance(op, migrations.RenameModel)
        and migration.app_label == app_config.label
    ]

    if not renames:
        return

    planned = []
    conflicts = []

    for old_name, new_name in renames:
        old_suffix = f"_{old_name.lower()}"
        new_suffix = f"_{new_name.lower()}"

        actions, verbose_name_raw = _get_permission_metadata(apps, app_label, new_name)
        perms = Permission.objects.using(db).filter(
            content_type__app_label=app_label,
            codename__in=[f"{action}{old_suffix}" for action in actions],
        )

        for perm in perms:
            for action in actions:
                if not perm.codename.startswith(action + "_"):
                    continue

                old_codename = perm.codename
                new_codename = f"{action}{new_suffix}"
                new_name_str = f"Can {action} {verbose_name_raw}"

                planned.append((perm, old_codename, new_codename, new_name_str))

    existing = {
        p.codename
        for p in Permission.objects.using(db).filter(
            content_type__app_label=app_label,
            codename__in=[new for _, _, new, _ in planned],
        )
    }

    # Look for conflicts
    for perm, old, new, _ in planned:
        if new in existing and perm.codename != new:
            conflicts.append((perm.pk, old, new))

    # Raise error if conflicts found
    if conflicts:
        if verbosity:
            style = color_style()
            for pk, old, new in conflicts:
                msg = (
                    f"Failed to rename permission {pk} from '{old}' to '{new}'. "
                    f"Please resolve the conflict manually.\n"
                )
                stdout.write(style.WARNING(msg))
        error_message = f"{len(conflicts)} permission rename conflict(s) detected."
        raise RuntimeError(error_message)

    with transaction.atomic(using=db):
        for perm, _, new_codename, new_name_str in planned:
            perm.codename = new_codename
            perm.name = new_name_str
            perm.save(update_fields={"codename", "name"}, using=db)

    for _, from_codename, to_codename, _ in planned:
        if verbosity >= 2:
            stdout.write(
                f"Renamed permission(s): "
                f"{app_label}.{from_codename} → {to_codename}\n"
            )