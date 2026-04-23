def validate_field_schema(trigger_schema: dict[str, Any]) -> dict[str, Any]:
    """Validate a field schema including context references."""

    for field_name, field_schema in trigger_schema.get("fields", {}).items():
        # Validate context if present
        if "context" in field_schema:
            if CONF_SELECTOR not in field_schema:
                raise vol.Invalid(
                    f"Context defined without a selector in '{field_name}'"
                )

            context = field_schema["context"]
            if not isinstance(context, dict):
                raise vol.Invalid(f"Context must be a dictionary in '{field_name}'")

            # Determine which selector type is being used
            selector_config = field_schema[CONF_SELECTOR]
            selector_class = selector.selector(selector_config)

            for context_key, field_ref in context.items():
                # Check if context key is allowed for this selector type
                allowed_keys = selector_class.allowed_context_keys
                if context_key not in allowed_keys:
                    raise vol.Invalid(
                        f"Invalid context key '{context_key}' for selector type '{selector_class.selector_type}'. "
                        f"Allowed keys: {', '.join(sorted(allowed_keys)) if allowed_keys else 'none'}"
                    )

                # Check if the referenced field exists in trigger schema or target
                if not isinstance(field_ref, str):
                    raise vol.Invalid(
                        f"Context value for '{context_key}' must be a string field reference"
                    )

                # Check if field exists in trigger schema fields or target
                trigger_fields = trigger_schema["fields"]
                field_exists = field_ref in trigger_fields
                if field_exists and "selector" in trigger_fields[field_ref]:
                    # Check if the selector type is allowed for this context key
                    field_selector_config = trigger_fields[field_ref][CONF_SELECTOR]
                    field_selector_class = selector.selector(field_selector_config)
                    if field_selector_class.selector_type not in allowed_keys.get(
                        context_key, set()
                    ):
                        raise vol.Invalid(
                            f"The context '{context_key}' for '{field_name}' references '{field_ref}', but '{context_key}' "
                            f"does not allow selectors of type '{field_selector_class.selector_type}'. Allowed selector types: {', '.join(allowed_keys.get(context_key, set()))}"
                        )
                if not field_exists and "target" in trigger_schema:
                    # Target is a special field that always exists when defined
                    field_exists = field_ref == "target"
                    if field_exists and "target" not in allowed_keys.get(
                        context_key, set()
                    ):
                        raise vol.Invalid(
                            f"The context '{context_key}' for '{field_name}' references 'target', but '{context_key}' "
                            f"does not allow 'target'. Allowed selector types: {', '.join(allowed_keys.get(context_key, set()))}"
                        )

                if not field_exists:
                    raise vol.Invalid(
                        f"Context reference '{field_ref}' for key '{context_key}' does not exist "
                        f"in trigger schema fields or target"
                    )

    return trigger_schema