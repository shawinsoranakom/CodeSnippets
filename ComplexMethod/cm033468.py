def compare_fields(model_fields: dict, db_columns: dict) -> dict:
    """Compare model fields with database columns

    Returns:
        dict: {
            'added': {field_name: field_obj},  # New fields not in DB
            'changed': {field_name: (old_info, new_field)},  # Type changed
            'removed': {field_name: col_info},  # Fields in DB but not in model
        }
    """
    result = {
        'added': {},
        'changed': {},
        'removed': {},
    }

    # Skip auto-generated fields like id, create_time, etc.
    skip_fields = {'id'}

    for field_name, field in model_fields.items():
        if field_name in skip_fields:
            continue

        # Check if field exists in database
        if field_name not in db_columns:
            result['added'][field_name] = field
            logger.info(f"  New field detected: {field_name} ({field.__class__.__name__})")
        else:
            # Check if type changed
            db_col = db_columns[field_name]
            model_base_type = normalize_field_type(field)
            db_type = db_col['peewee_type']

            # Type mismatch
            if model_base_type != db_type:
                result['changed'][field_name] = (db_col, field)
                logger.info(f"  Field type changed: {field_name} ({db_type} -> {model_base_type}, actual: {field.__class__.__name__})")

    # Detect removed fields: columns in DB but not in model
    for col_name, col_info in db_columns.items():
        if col_name in skip_fields:
            continue
        if col_name not in model_fields:
            result['removed'][col_name] = col_info
            logger.info(f"  Removed field detected: {col_name} ({col_info['column_type']})")

    return result