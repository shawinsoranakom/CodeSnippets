def generate_migration_content(new_tables: list, field_changes: dict, migrate_dir: str, migration_name: str, drop_fields: bool = False) -> str:
    """Generate migration file content"""
    lines = [
        '"""Peewee migrations."""',
        '',
        'from contextlib import suppress',
        '',
        'import peewee as pw',
        'from peewee_migrate import Migrator',
        '',
        '',
        'with suppress(ImportError):',
        '    import playhouse.postgres_ext as pw_pext',
        '',
        '',
        'def migrate(migrator: Migrator, database: pw.Database, *, fake=False):',
        '    """Write your migrations here."""',
        '',
    ]

    # Generate create_model for new tables
    for model in new_tables:
        table_name = model._meta.table_name
        model_name = model.__name__

        lines.append('    @migrator.create_model')
        lines.append(f'    class {model_name}(pw.Model):')

        # Get all fields
        fields = model._meta.fields
        for field_name, field in fields.items():
            field_code = generate_field_code(field, field_name)
            lines.append(f'        {field_name} = {field_code}')

        lines.append('')
        lines.append('        class Meta:')
        lines.append(f'            table_name = "{table_name}"')

        # Add indexes if defined
        indexes = getattr(model._meta, 'indexes', None)
        if indexes:
            lines.append(f'            indexes = {indexes}')

        lines.append('')

    # Generate SQL for adding new fields to existing tables
    for table_name, changes in field_changes.items():
        if changes.get('added'):
            for field_name, field in changes['added'].items():
                sql, index_sql = generate_add_field_sql(table_name, field, field_name)
                lines.append(f'    migrator.sql("{sql}")')
                if index_sql:
                    lines.append(f'    migrator.sql("{index_sql}")')
                lines.append('')

    # Generate SQL for modifying fields in existing tables
    for table_name, changes in field_changes.items():
        if changes.get('changed'):
            for field_name, (old_info, field) in changes['changed'].items():
                modify_sql = generate_modify_field_sql(table_name, field, field_name)
                lines.append(f'    migrator.sql("{modify_sql}")')
                lines.append('')

    # Generate SQL for dropping removed fields from existing tables
    if drop_fields:
        for table_name, changes in field_changes.items():
            if changes.get('removed'):
                for field_name, col_info in changes['removed'].items():
                    drop_sql = generate_drop_field_sql(table_name, field_name)
                    lines.append(f'    # WARNING: Dropping column `{field_name}` from `{table_name}` - this will permanently delete data!')
                    lines.append(f'    migrator.sql("{drop_sql}")')
                    lines.append('')

    # Generate rollback
    lines.append('')
    lines.append('def rollback(migrator: Migrator, database: pw.Database, *, fake=False):')
    lines.append('    """Write your rollback migrations here."""')
    lines.append('')

    # Rollback: re-add dropped fields (before other rollbacks, since they may depend on these fields)
    if drop_fields:
        for table_name, changes in field_changes.items():
            if changes.get('removed'):
                for field_name, col_info in changes['removed'].items():
                    add_sql, index_sql = generate_rollback_add_field_sql(table_name, col_info, field_name)
                    lines.append(f'    # Re-add dropped column `{field_name}` to `{table_name}` (data is lost)')
                    lines.append(f'    migrator.sql("{add_sql}")')
                    if index_sql:
                        lines.append(f'    migrator.sql("{index_sql}")')

    # Rollback: reverse field type changes first (before removing added fields)
    for table_name, changes in field_changes.items():
        if changes.get('changed'):
            for field_name, (old_info, field) in changes['changed'].items():
                rollback_modify_sql = generate_rollback_modify_sql(table_name, old_info, field_name)
                lines.append('    # Note: Data values may need manual handling if type conversion caused data loss')
                lines.append(f'    migrator.sql("{rollback_modify_sql}")')

    # Rollback: remove added fields using SQL
    for table_name, changes in field_changes.items():
        if changes.get('added'):
            for field_name in changes['added'].keys():
                rollback_sql = generate_rollback_field_sql(table_name, field_name)
                lines.append(f'    migrator.sql("{rollback_sql}")')

    # Rollback: remove tables (in reverse order)
    for model in reversed(new_tables):
        table_name = model._meta.table_name
        lines.append(f'    migrator.remove_model("{table_name}")')

    lines.append('')

    return '\n'.join(lines)