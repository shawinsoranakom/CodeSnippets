def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        """Update build configuration to add dynamic inputs that can connect to other components."""
        if field_name == "form_fields":
            # Clear existing dynamic inputs from build config
            keys_to_remove = [key for key in build_config if key.startswith("dynamic_")]
            for key in keys_to_remove:
                del build_config[key]

            # Add dynamic inputs based on table configuration
            # Safety check to ensure field_value is not None and is iterable
            if field_value is None:
                field_value = []

            for i, field_config in enumerate(field_value):
                # Safety check to ensure field_config is not None
                if field_config is None:
                    continue

                field_name = field_config.get("field_name", f"field_{i}")
                display_name = field_name  # Use field_name as display_name
                field_type_option = field_config.get("field_type", "Text")
                default_value = ""  # All fields have empty default value
                required = False  # All fields are optional by default
                help_text = ""  # All fields have empty help text

                # Map field type options to actual field types and input types
                field_type_mapping = {
                    "Text": {"field_type": "multiline", "input_types": ["Text", "Message"]},
                    "Data": {"field_type": "data", "input_types": ["Data"]},
                    "Number": {"field_type": "number", "input_types": ["Text", "Message"]},
                    "Handle": {"field_type": "handle", "input_types": ["Text", "Data", "Message"]},
                    "Boolean": {"field_type": "boolean", "input_types": None},
                }

                field_config_mapped = field_type_mapping.get(
                    field_type_option, {"field_type": "text", "input_types": []}
                )
                if not isinstance(field_config_mapped, dict):
                    field_config_mapped = {"field_type": "text", "input_types": []}
                field_type = field_config_mapped["field_type"]
                input_types_list = field_config_mapped["input_types"]

                # Create the appropriate input type based on field_type
                dynamic_input_name = f"dynamic_{field_name}"

                if field_type == "text":
                    if input_types_list:
                        build_config[dynamic_input_name] = StrInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=f"{help_text} (Can connect to: {', '.join(input_types_list)})",
                            value=default_value,
                            required=required,
                            input_types=input_types_list,
                        )
                    else:
                        build_config[dynamic_input_name] = StrInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=help_text,
                            value=default_value,
                            required=required,
                        )

                elif field_type == "multiline":
                    if input_types_list:
                        build_config[dynamic_input_name] = MultilineInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=f"{help_text} (Can connect to: {', '.join(input_types_list)})",
                            value=default_value,
                            required=required,
                            input_types=input_types_list,
                        )
                    else:
                        build_config[dynamic_input_name] = MultilineInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=help_text,
                            value=default_value,
                            required=required,
                        )

                elif field_type == "number":
                    try:
                        default_int = int(default_value) if default_value else 0
                    except ValueError:
                        default_int = 0

                    if input_types_list:
                        build_config[dynamic_input_name] = IntInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=f"{help_text} (Can connect to: {', '.join(input_types_list)})",
                            value=default_int,
                            required=required,
                            input_types=input_types_list,
                        )
                    else:
                        build_config[dynamic_input_name] = IntInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=help_text,
                            value=default_int,
                            required=required,
                        )

                elif field_type == "float":
                    try:
                        default_float = float(default_value) if default_value else 0.0
                    except ValueError:
                        default_float = 0.0

                    if input_types_list:
                        build_config[dynamic_input_name] = FloatInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=f"{help_text} (Can connect to: {', '.join(input_types_list)})",
                            value=default_float,
                            required=required,
                            input_types=input_types_list,
                        )
                    else:
                        build_config[dynamic_input_name] = FloatInput(
                            name=dynamic_input_name,
                            display_name=display_name,
                            info=help_text,
                            value=default_float,
                            required=required,
                        )

                elif field_type == "boolean":
                    default_bool = default_value.lower() in ["true", "1", "yes"] if default_value else False

                    # Boolean fields don't use input_types parameter to avoid errors
                    build_config[dynamic_input_name] = BoolInput(
                        name=dynamic_input_name,
                        display_name=display_name,
                        info=help_text,
                        value=default_bool,
                        input_types=[],
                        required=required,
                    )

                elif field_type == "handle":
                    # HandleInput for generic data connections
                    build_config[dynamic_input_name] = HandleInput(
                        name=dynamic_input_name,
                        display_name=display_name,
                        info=f"{help_text} (Accepts: {', '.join(input_types_list) if input_types_list else 'Any'})",
                        input_types=input_types_list if input_types_list else ["Data", "Text", "Message"],
                        required=required,
                    )

                elif field_type == "data":
                    # Specialized for Data type connections
                    build_config[dynamic_input_name] = HandleInput(
                        name=dynamic_input_name,
                        display_name=display_name,
                        info=f"{help_text} (Data input)",
                        input_types=input_types_list if input_types_list else ["Data"],
                        required=required,
                    )

                else:
                    # Default to text input for unknown types
                    build_config[dynamic_input_name] = StrInput(
                        name=dynamic_input_name,
                        display_name=display_name,
                        info=f"{help_text} (Unknown type '{field_type}', defaulting to text)",
                        value=default_value,
                        required=required,
                    )

        return build_config