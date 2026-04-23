def generate_modify_field_sql(table_name: str, field: Field, field_name: str) -> str:
    """Generate SQL for modifying a field in MySQL table."""
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

    return f"ALTER TABLE `{table_name}` MODIFY COLUMN {' '.join(parts)}"