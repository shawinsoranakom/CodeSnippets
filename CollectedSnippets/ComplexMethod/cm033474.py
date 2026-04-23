def create_migration(router: Router, models: list, db, name: str = "auto", drop_fields: bool = False):
    """Create a new migration by auto-detecting model changes

    Detects:
    1. New tables -> generate create_model
    2. New fields in existing tables -> generate add_fields
    3. Field type changes -> generate change_fields
    4. Removed fields (only when --drop is specified) -> generate drop_fields

    Args:
        router: peewee-migrate Router instance
        models: List of model classes to compare against database
        db: Database connection
        name: Migration name
        drop_fields: Whether to include DROP COLUMN for removed fields
    """
    try:
        # Get existing tables from database
        cursor = db.execute_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            (db.database,)
        )
        existing_tables = {row[0] for row in cursor.fetchall()}

        new_tables = []
        field_changes = {}

        for model in models:
            table_name = model._meta.table_name

            if table_name not in existing_tables:
                # New table
                new_tables.append(model)
                logger.info(f"New table detected: {table_name}")
            else:
                # Existing table - check for field changes
                logger.info(f"Checking existing table: {table_name}")

                # Get model fields (exclude auto-generated)
                model_fields = {}
                for field_name, field in model._meta.fields.items():
                    # Skip id and base model fields
                    if field_name in ('id', 'create_time', 'create_date', 'update_time', 'update_date'):
                        continue
                    if hasattr(field, '_auto_created') and field._auto_created:
                        continue
                    model_fields[field_name] = field

                # Get database columns
                db_columns = get_table_columns(db, table_name)

                # Compare
                changes = compare_fields(model_fields, db_columns)

                if changes['added'] or changes['changed'] or changes['removed']:
                    field_changes[table_name] = changes

        # Check if any changes detected
        has_removed = any(changes.get('removed') for changes in field_changes.values())
        if not drop_fields and has_removed:
            removed_details = []
            for table_name, changes in field_changes.items():
                if changes.get('removed'):
                    for col_name in changes['removed']:
                        removed_details.append(f"{table_name}.{col_name}")
            logger.warning(f"Removed fields detected (not included in migration, use --drop to include): {', '.join(removed_details)}")
            # Remove 'removed' from changes since we're not acting on them
            for table_name in field_changes:
                field_changes[table_name]['removed'] = {}

        if not new_tables and not any(changes['added'] or changes['changed'] for changes in field_changes.values()):
            if not (drop_fields and has_removed):
                logger.info("No schema changes detected, migration not created")
                return None

        # Generate migration file content
        migration_content = generate_migration_content(new_tables, field_changes, router.migrate_dir, name, drop_fields=drop_fields)

        # Get next migration number (count existing migration files)
        existing_migrations = [f for f in os.listdir(router.migrate_dir) if f.endswith('.py') and not f.startswith('_')]
        migration_num = len(existing_migrations) + 1
        migration_file = os.path.join(router.migrate_dir, f'{migration_num:03d}_{name}.py')

        with open(migration_file, 'w') as f:
            f.write(migration_content)

        logger.info(f"Created migration: {migration_file}")
        return migration_file

    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise