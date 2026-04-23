def diff_schema(models: list, db):
    """Show schema differences between models and database"""
    logger.info("Checking schema differences...")

    # Tables to ignore (managed by peewee-migrate)
    IGNORE_TABLES = {'migratehistory'}

    # Get all model table names
    model_tables = set()
    for model in models:
        table_name = model._meta.table_name
        model_tables.add(table_name)

    logger.info(f"Found {len(model_tables)} model tables")

    # Get existing tables from database
    cursor = db.execute_sql(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
        (db.database,)
    )
    existing_tables = {row[0] for row in cursor.fetchall() if row[0] not in IGNORE_TABLES}

    # Find tables that exist in models but not in database
    missing_tables = model_tables - existing_tables
    if missing_tables:
        logger.warning(f"Tables not in database ({len(missing_tables)}): {', '.join(sorted(missing_tables))}")

    # Find tables that exist in database but not in models
    extra_tables = existing_tables - model_tables
    if extra_tables:
        logger.info(f"Tables in database but not in models: {', '.join(sorted(extra_tables))}")

    # Check field differences for existing tables
    common_tables = model_tables & existing_tables
    if common_tables:
        logger.info(f"\nChecking field differences for {len(common_tables)} existing tables...")

        total_added = 0
        total_changed = 0
        total_removed = 0

        for model in models:
            table_name = model._meta.table_name
            if table_name not in common_tables:
                continue

            # Get model fields
            model_fields = {}
            for field_name, field in model._meta.fields.items():
                if field_name in ('id', 'create_time', 'create_date', 'update_time', 'update_date'):
                    continue
                model_fields[field_name] = field

            # Get database columns
            db_columns = get_table_columns(db, table_name)

            # Compare
            changes = compare_fields(model_fields, db_columns)

            if changes['added']:
                total_added += len(changes['added'])
                field_details = [f"{k}:{v.__class__.__name__}" for k, v in changes['added'].items()]
                logger.info(f"  {table_name}: {len(changes['added'])} new field(s) - {field_details}")

            if changes['changed']:
                total_changed += len(changes['changed'])
                field_details = [f"{k}:{v[1].__class__.__name__}" for k, v in changes['changed'].items()]
                logger.info(f"  {table_name}: {len(changes['changed'])} changed field(s) - {field_details}")

            if changes['removed']:
                total_removed += len(changes['removed'])
                field_details = [f"{k}:{v['column_type']}" for k, v in changes['removed'].items()]
                logger.warning(f"  {table_name}: {len(changes['removed'])} removed field(s) - {field_details}")

        logger.info(f"\nSummary: {total_added} new fields, {total_changed} changed fields, {total_removed} removed fields")