def _get_provider_field_params(
        cls, model: str, params_type: str, provider: str = "openbb"
    ) -> list[dict[str, Any]]:
        """Get the fields of the given parameter type for the given provider of the standard_model."""
        provider_field_params = []
        expanded_types = MethodDefinition.TYPE_EXPANSION
        model_map = cls.pi.map[model]

        # First, check if the provider class itself has __json_schema_extra__
        # This contains class-level schema information that applies to fields
        class_schema_extra = {}
        try:
            # Get the actual provider class
            provider_class = model_map[provider][params_type]["class"]
            # Check for class-level __json_schema_extra__ attribute
            if hasattr(provider_class, "__json_schema_extra__"):
                class_schema_extra = provider_class.__json_schema_extra__
        except (KeyError, AttributeError):
            pass

        for field, field_info in model_map[provider][params_type]["fields"].items():
            # Start with class-level schema information for this field if it exists
            extra = {}
            choices = None
            if field in class_schema_extra:
                extra = class_schema_extra[field].copy()
                choices = extra.get("choices")

            # Then apply field-level schema extra (which takes precedence)
            field_extra = field_info.json_schema_extra or {}
            extra.update(field_extra)
            if "choices" in field_extra:
                choices = field_extra.pop("choices", [])

            if provider != "openbb" and provider in extra:
                extra = extra[provider]

            # Determine the field type, expanding it if necessary
            field_type = field_info.annotation
            is_required = field_info.is_required()

            origin = get_origin(field_type)
            if origin is Union:
                args = get_args(field_type)
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    field_type = non_none_types[0]
                if type(None) in args:
                    is_required = False

            # Then unwrap Annotated
            while get_origin(field_type) is Annotated:
                args = get_args(field_type)
                if args:
                    field_type = args[0]
                else:
                    break

            field_type_str = DocstringGenerator.get_field_type(
                field_type, is_required, "website"
            )

            if field_type_str == "Annotated | None" or field_type_str.startswith(
                "Annotated"
            ):
                # If we still have "Annotated" in the string, extract the actual type
                if hasattr(field_type, "__name__") or isinstance(field_type, type):
                    field_type_str = field_type.__name__
                else:
                    # Last resort: try to parse from string representation
                    type_repr = str(field_type).replace("typing.", "")
                    if "Annotated[" in type_repr:
                        # Extract the first type argument
                        match = re.search(r"Annotated\[([^,\]]+)", type_repr)
                        if match:
                            field_type_str = match.group(1)
                    else:
                        field_type_str = type_repr

            if is_required is False and "| None" not in field_type_str:
                field_type_str = f"{field_type_str} | None"

            # Handle case where field_type_str contains ", optional" suffix
            if ", optional" in field_type_str:
                field_type_str = field_type_str.replace(", optional", "")
                is_required = False

            cleaned_description = str(field_info.description).strip().replace('"', "'")

            # Add information for the providers supporting multiple symbols
            if params_type == "QueryParams" and extra:
                providers: list = []
                for p, v in extra.items():
                    if isinstance(v, dict) and v.get("multiple_items_allowed"):
                        providers.append(p)
                        if "choices" in v:
                            choices = v.get("choices")
                    elif isinstance(v, list) and "multiple_items_allowed" in v:
                        providers.append(p)
                    elif isinstance(v, dict) and "choices" in v:
                        choices = v.get("choices")

                if providers or extra.get("multiple_items_allowed"):
                    cleaned_description += " Multiple items allowed"
                    if providers:
                        multiple_items = ", ".join(providers)
                        cleaned_description += f" for provider(s): {multiple_items}"
                    cleaned_description += "."
                    field_type_str = f"{field_type_str} | list[{field_type_str}]"
            elif field in expanded_types:
                expanded_type = DocstringGenerator.get_field_type(
                    expanded_types[field], is_required, "website"
                )
                field_type_str = f"{field_type_str} | {expanded_type}"

            default_value = (
                None if field_info.default is PydanticUndefined else field_info.default
            )
            if default_value == "":
                default_value = None

            to_append = {
                "name": field,
                "type": field_type_str,
                "description": cleaned_description,
                "default": default_value,
                "optional": not is_required,
            }
            if params_type != "Data":
                to_append.update(
                    {
                        "choices": choices or extra.pop("choices", []),
                        "multiple_items_allowed": extra.pop(
                            "multiple_items_allowed", False
                        ),
                        "json_schema_extra": extra or {},
                    }
                )
            else:
                to_append.update({"json_schema_extra": extra or {}})
            provider_field_params.append(to_append)

        return provider_field_params