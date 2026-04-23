def generate_field_code(field: Field, field_name: str) -> str:
    """Generate peewee field definition code"""
    field_class = field.__class__.__name__

    # Map custom field types to standard peewee types for migration
    # These custom types will be stored as their underlying standard type
    custom_to_standard = {
        'LongTextField': 'TextField',
        'JSONField': 'TextField',
        'ListField': 'TextField',
        'SerializedField': 'TextField',
        'DateTimeTzField': 'CharField',
    }

    # Use standard type for custom fields
    pw_field_class = custom_to_standard.get(field_class, field_class)

    # Build field arguments
    args = []

    # max_length for CharField
    if pw_field_class == 'CharField' and hasattr(field, 'max_length') and field.max_length is not None:
        args.append(f"max_length={field.max_length}")

    # null
    if field.null:
        args.append("null=True")

    # default
    if field.default is not None:
        default_val = field.default
        if isinstance(default_val, str):
            # Escape quotes in string
            escaped = default_val.replace("'", "\\'")
            args.append(f"default='{escaped}'")
        elif isinstance(default_val, bool):
            args.append(f"default={'True' if default_val else 'False'}")
        elif isinstance(default_val, (int, float)):
            args.append(f"default={default_val}")
        elif isinstance(default_val, dict):
            args.append(f"default={default_val}")
        elif isinstance(default_val, list):
            args.append(f"default={default_val}")

    # index
    if getattr(field, 'index', False):
        args.append("index=True")

    # unique
    if getattr(field, 'unique', False):
        args.append("unique=True")

    args_str = ', '.join(args)
    return f"pw.{pw_field_class}({args_str})"