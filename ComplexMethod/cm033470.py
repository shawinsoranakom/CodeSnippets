def generate_add_field_sql(table_name: str, field: Field, field_name: str) -> str:
    """Generate raw SQL for adding a field to MySQL table.

    This is used for existing tables where migrator.add_fields doesn't work
    because the model is not registered in migrator.orm.
    """
    field_class = field.__class__.__name__

    # Determine MySQL column type
    mysql_type_map = {
        'CharField': f'VARCHAR({field.max_length})' if hasattr(field, 'max_length') and field.max_length else 'VARCHAR(255)',
        'TextField': 'LONGTEXT',
        'LongTextField': 'LONGTEXT',
        'JSONField': 'LONGTEXT',
        'ListField': 'LONGTEXT',
        'SerializedField': 'LONGTEXT',
        'IntegerField': 'INT',
        'BigIntegerField': 'BIGINT',
        'FloatField': 'DOUBLE',
        'BooleanField': 'TINYINT(1)',
        'DateTimeField': 'DATETIME',
        'DateTimeTzField': f'VARCHAR({field.max_length})' if hasattr(field, 'max_length') and field.max_length else 'VARCHAR(255)',
    }

    mysql_type = mysql_type_map.get(field_class, 'LONGTEXT')

    # Build column definition
    parts = [f'`{field_name}`', mysql_type]

    # NULL/NOT NULL
    if field.null:
        parts.append('NULL')
    else:
        parts.append('NOT NULL')

    # DEFAULT
    if field.default is not None:
        default_val = field.default
        if isinstance(default_val, str):
            escaped = default_val.replace("'", "''")
            parts.append(f"DEFAULT '{escaped}'")
        elif isinstance(default_val, bool):
            parts.append(f"DEFAULT {1 if default_val else 0}")
        elif isinstance(default_val, (int, float)):
            parts.append(f"DEFAULT {default_val}")
        elif isinstance(default_val, dict) or isinstance(default_val, list):
            import json
            escaped = json.dumps(default_val).replace("'", "''")
            parts.append(f"DEFAULT '{escaped}'")

    # COMMENT
    if hasattr(field, 'help_text') and field.help_text:
        escaped = field.help_text.replace("'", "''")
        parts.append(f"COMMENT '{escaped}'")

    sql = f"ALTER TABLE `{table_name}` ADD COLUMN {' '.join(parts)}"

    # Add index if needed
    index_sql = None
    if getattr(field, 'index', False):
        index_sql = f"CREATE INDEX `idx_{table_name}_{field_name}` ON `{table_name}` (`{field_name}`)"

    return sql, index_sql