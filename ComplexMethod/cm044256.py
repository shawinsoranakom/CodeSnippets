def _create_field(
        name: str,
        field: FieldInfo,
        provider_name: str | None = None,
        query: bool = False,
        force_optional: bool = False,
    ) -> DataclassField:
        new_name = name.replace(".", "_")
        annotation = field.annotation

        additional_description = ""
        choices: dict = {}
        if extra := field.json_schema_extra:
            providers: list = []
            for p, v in extra.items():  # type: ignore
                if isinstance(v, dict) and v.get("multiple_items_allowed"):
                    providers.append(p)
                    choices[p] = {"multiple_items_allowed": True, "choices": v.get("choices")}  # type: ignore
                elif isinstance(v, list) and "multiple_items_allowed" in v:
                    # For backwards compatibility, before this was a list
                    providers.append(p)
                    choices[p] = {"multiple_items_allowed": True, "choices": None}  # type: ignore
                elif isinstance(v, dict) and v.get("choices"):
                    choices[p] = {
                        "multiple_items_allowed": False,
                        "choices": v.get("choices"),
                    }

                if isinstance(v, dict) and v.get("x-widget_config"):
                    if p not in choices:
                        choices[p] = {"x-widget_config": v.get("x-widget_config")}
                    else:
                        choices[p]["x-widget_config"] = v.get("x-widget_config")

            if providers:
                if provider_name:
                    additional_description += " Multiple comma separated items allowed."
                else:
                    additional_description += (
                        " Multiple comma separated items allowed for provider(s): "
                        + ", ".join(providers)  # type: ignore[arg-type]
                        + "."
                    )

        # Auto-derive choices from Literal annotation for provider-specific fields
        # when no explicit choices are already declared for this provider.
        # This makes Literal annotations equivalent to manually declared choices,
        # so providers only need to declare the type annotation.
        if provider_name and provider_name not in choices:
            _ann = annotation
            _origin = get_origin(_ann)
            # Unwrap Optional[Literal[...]] = Union[Literal[...], None]
            if _origin is Union:
                _inner = [a for a in get_args(_ann) if a is not type(None)]
                if len(_inner) == 1:
                    _ann = _inner[0]
                    _origin = get_origin(_ann)
            if _origin is Literal:
                _literal_args = list(get_args(_ann))
                if _literal_args:
                    choices[provider_name] = {
                        "choices": _literal_args,
                    }

        provider_field = (
            f"(provider: {provider_name})" if provider_name != "openbb" else ""
        )
        description = (
            f"{field.description}{additional_description} {provider_field}"
            if provider_name and field.description
            else f"{field.description}{additional_description}"
        )

        if field.is_required():
            if force_optional:
                annotation = Optional[annotation]  # type: ignore  # noqa
                default = None
            else:
                default = ...
        else:
            default = field.default

        if (
            hasattr(annotation, "__name__")
            and annotation.__name__ in ["Dict", "dict", "Data"]  # type: ignore
            or field.kw_only is True
        ):
            return DataclassField(
                new_name,
                annotation,
                Body(
                    default=default,
                    title=provider_name,
                    description=description,
                    alias=field.alias or None,
                    json_schema_extra=choices,
                ),
            )

        if query:
            # We need to use query if we want the field description to show
            # up in the swagger, it's a fastapi limitation
            return DataclassField(
                new_name,
                annotation,
                Query(
                    default=default,
                    title=provider_name,
                    description=description,
                    alias=field.alias or None,
                    json_schema_extra=choices,
                ),
            )
        if provider_name:
            return DataclassField(
                new_name,
                annotation,
                Field(
                    default=default or None,
                    title=provider_name,
                    description=description,
                    json_schema_extra=choices,
                ),
            )

        return DataclassField(new_name, annotation, default)