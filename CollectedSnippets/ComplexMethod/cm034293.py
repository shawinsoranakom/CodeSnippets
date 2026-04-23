def convert_field(cls, resolved_field: ResolvedField, value: object) -> object:
        if value is None:
            return None if resolved_field.optional else resolved_field.field.default

        if resolved_field.type is _messages.ErrorSummary:
            return value  # RPFIX-5: VALIDATION: defer conversion to __post_init__

        # RPFIX-5: VALIDATION: this doesn't handle special types like exception which require extra conversion

        if not resolved_field.metadata.conversion_func and isinstance(value, resolved_field.type):
            return value

        # RPFIX-5: VALIDATION: this type checking doesn't validate types within containers (mapping, dict, etc.)

        help_text = f"Values for result key {resolved_field.result_key!r} must be of type {native_type_name(resolved_field.type)}."

        conversion_func = resolved_field.metadata.conversion_func or resolved_field.type

        try:
            result = conversion_func(value)
        except Exception:
            result = resolved_field.field.default
            display.warning(
                f'Value for result key {resolved_field.result_key!r} of type {native_type_name(value)} was replaced with {result}.',
                obj=value,
                help_text=help_text,
            )
        else:
            if not isinstance(value, resolved_field.type):
                # RPFIX-5: UX: this will still give duplicate warnings -- probably just need to be explicit and have conversion funcs do warnings
                display.warning(
                    msg=f'Value for result key {resolved_field.result_key!r} of type {native_type_name(value)} '
                    f'was converted to {native_type_name(resolved_field.type)}.',
                    obj=value,
                    help_text=help_text,
                )

        return result