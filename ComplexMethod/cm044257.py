def _extract_params(
        cls,
        providers: Any,
    ) -> tuple[dict[str, TupleFieldType], dict[str, TupleFieldType]]:
        """Extract parameters from map."""
        standard: dict[str, TupleFieldType] = {}
        extra: dict[str, TupleFieldType] = {}
        standard_fields = (
            providers.get("openbb", {}).get("QueryParams", {}).get("fields", {})
        )

        for provider_name, model_details in providers.items():
            if provider_name == "openbb":
                for name, field in model_details["QueryParams"]["fields"].items():
                    incoming = cls._create_field(name, field, query=True)

                    standard[incoming.name] = (
                        incoming.name,
                        incoming.annotation,
                        incoming.default,
                    )
            else:
                for name, field in model_details["QueryParams"]["fields"].items():
                    s_name = to_snake_case(name)

                    if name in standard_fields:
                        # Provider redefines a standard field - merge descriptions
                        # Check if descriptions differ before merging
                        standard_desc = standard_fields[name].description or ""
                        provider_desc = field.description or ""

                        if provider_desc and provider_desc != standard_desc:
                            # Create a field with provider-specific description
                            incoming = cls._create_field(
                                s_name,
                                field,
                                provider_name,
                                query=True,
                                force_optional=False,
                            )
                            # Merge into the standard field
                            if s_name in standard:
                                current = DataclassField(*standard[s_name])
                                updated = cls._merge_fields(
                                    current, incoming, query=True
                                )
                                standard[s_name] = (
                                    updated.name,
                                    updated.annotation,
                                    updated.default,
                                )
                    else:
                        # Extra field not in standard - add to extra params
                        incoming = cls._create_field(
                            s_name,
                            field,
                            provider_name,
                            query=True,
                            force_optional=True,
                        )

                        if incoming.name in extra:
                            current = DataclassField(*extra[incoming.name])
                            updated = cls._merge_fields(current, incoming, query=True)
                        else:
                            updated = incoming

                        extra[updated.name] = (
                            updated.name,
                            updated.annotation,
                            updated.default,
                        )

        return standard, extra