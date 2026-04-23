def key_value_validator(value: Any) -> dict[Hashable, Any]:
        if not isinstance(value, dict):
            raise vol.Invalid("Expected a dictionary")

        key_value = value.get(key)

        if isinstance(key_value, Hashable) and key_value in value_schemas:
            return cast(dict[Hashable, Any], value_schemas[key_value](value))

        if default_schema:
            with contextlib.suppress(vol.Invalid):
                return cast(dict[Hashable, Any], default_schema(value))

        if list_alternatives:
            alternatives = ", ".join(str(alternative) for alternative in value_schemas)
            if default_description:
                alternatives = f"{alternatives}, {default_description}"
        else:
            # mypy does not understand that default_description is not None here
            alternatives = default_description  # type: ignore[assignment]
        raise vol.Invalid(
            f"Unexpected value for {key}: '{key_value}'. Expected {alternatives}"
        )