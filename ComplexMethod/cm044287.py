def add_field_custom_annotations(
        od: OrderedDict[str, Parameter], model_name: str | None = None
    ):
        """Add the field custom description and choices to the param signature as annotations."""
        if not model_name:
            return

        provider_interface = ProviderInterface()

        # Get fields from standard model
        try:
            available_fields = provider_interface.params[model_name][
                "standard"
            ].__dataclass_fields__
            extra_fields = provider_interface.params[model_name][
                "extra"
            ].__dataclass_fields__
        except (KeyError, AttributeError):
            return

        # Combined fields
        all_fields: dict = {}
        all_fields.update(available_fields)
        all_fields.update(extra_fields)

        for param, value in od.items():
            if param not in all_fields:
                continue

            field_default = all_fields[param].default
            extra = MethodDefinition.get_extra(all_fields[param])
            choices = getattr(all_fields[param], "json_schema_extra", {}).get(
                "choices", []
            ) or extra.get("choices", [])
            description = getattr(field_default, "description", "")

            # Handle provider-specific choices and add them to the description
            provider_specific: dict = {}
            for provider, provider_info in extra.items():
                if isinstance(provider_info, dict) and "choices" in provider_info:
                    provider_specific[provider] = provider_info["choices"]

            # Add provider-specific choices to description
            if provider_specific:
                # Add each provider's choices on a new line
                for provider, provider_choices in provider_specific.items():
                    if provider_choices:
                        choices_str = ", ".join(f"'{c}'" for c in provider_choices)
                        description += f"\nChoices for {provider}: {choices_str}"

            # Handle multiple_items_allowed
            multiple_items_providers: list = []
            for provider, provider_info in extra.items():
                if (
                    isinstance(provider_info, dict)
                    and provider_info.get("multiple_items_allowed")
                    or (
                        isinstance(provider_info, list)
                        and "multiple_items_allowed" in provider_info
                    )
                ):
                    multiple_items_providers.append(provider)

            if (
                multiple_items_providers
                and "Multiple comma separated items allowed for provider(s)"
                not in description
            ):
                description += f"\nMultiple items supported by: {', '.join(multiple_items_providers)}"

            # Process the field type - if it's a Union of many Literals, simplify to base type
            field_type = all_fields[param].type
            simplified_type = field_type

            # If there are provider-specific choices, try to simplify the type
            if (
                provider_specific
                and hasattr(field_type, "__origin__")
                and field_type.__origin__ is Union
            ):
                # Check if all union members are Literals
                all_literals = True
                for arg in field_type.__args__:
                    if not (hasattr(arg, "__origin__") and arg.__origin__ is Literal):
                        all_literals = False
                        break

                if all_literals:
                    # Find the base type of the literals (usually str or int)
                    literal_types = set()
                    for arg in field_type.__args__:
                        for lit_val in arg.__args__:
                            literal_types.add(type(lit_val))

                    # If all literals are of the same type, use that type
                    if len(literal_types) == 1:
                        simplified_type = next(iter(literal_types))

            # Create field with enhanced description and possibly simplified type
            field_kwargs = {
                "description": description,
            }

            if choices:
                field_kwargs["choices"] = choices

            new_value = value.replace(
                annotation=Annotated[
                    (
                        simplified_type
                        if simplified_type != field_type
                        else value.annotation
                    ),
                    OpenBBField(description=description),
                ],
            )

            od[param] = new_value