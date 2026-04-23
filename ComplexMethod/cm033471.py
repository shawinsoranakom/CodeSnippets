def generate_rollback_add_field_sql(table_name: str, col_info: dict, field_name: str) -> str:
    """Generate SQL for rolling back a dropped field (re-adding it).

    This reconstructs the ADD COLUMN statement from the column info
    that was captured before the field was dropped.
    """
    mysql_type = col_info.get('column_type', 'LONGTEXT')

    parts = [f'`{field_name}`', mysql_type]

    # NULL/NOT NULL
    if col_info.get('nullable', True):
        parts.append('NULL')
    else:
        parts.append('NOT NULL')

    # DEFAULT
    default_val = col_info.get('default')
    if default_val is not None:
        if isinstance(default_val, str):
            escaped = default_val.replace("'", "''")
            parts.append(f"DEFAULT '{escaped}'")
        elif isinstance(default_val, bool):
            parts.append(f"DEFAULT {1 if default_val else 0}")
        elif isinstance(default_val, (int, float)):
            parts.append(f"DEFAULT {default_val}")

    sql = f"ALTER TABLE `{table_name}` ADD COLUMN {' '.join(parts)}"

    # Re-add index if it was a non-primary key
    index_sql = None
    if col_info.get('column_key') == 'MUL':
        index_sql = f"CREATE INDEX `idx_{table_name}_{field_name}` ON `{table_name}` (`{field_name}`)"

    return sql, index_sql