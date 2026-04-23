def _extract_data(
        cls,
        providers: Any,
    ) -> tuple[dict[str, TupleFieldType], dict[str, TupleFieldType]]:
        standard: dict[str, TupleFieldType] = {}
        extra: dict[str, TupleFieldType] = {}

        for provider_name, model_details in providers.items():
            if provider_name == "openbb":
                for name, field in model_details["Data"]["fields"].items():
                    if (
                        name == "provider"
                        and field.description == "The data provider for the data."
                    ):  # noqa
                        continue
                    incoming = cls._create_field(name, field, "openbb")

                    standard[incoming.name] = (
                        incoming.name,
                        incoming.annotation,
                        incoming.default,
                    )
            else:
                for name, field in model_details["Data"]["fields"].items():
                    if name not in providers["openbb"]["Data"]["fields"]:
                        if (
                            name == "provider"
                            and field.description == "The data provider for the data."
                        ):  # noqa
                            continue
                        incoming = cls._create_field(
                            to_snake_case(name),
                            field,
                            provider_name,
                            force_optional=True,
                        )

                        if incoming.name in extra:
                            current = DataclassField(*extra[incoming.name])
                            updated = cls._merge_fields(current, incoming)
                        else:
                            updated = incoming

                        extra[updated.name] = (
                            updated.name,
                            updated.annotation,
                            updated.default,
                        )

        return standard, extra