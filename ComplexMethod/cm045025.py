def _coerce_input(
        name: str, value: Any, input_def: dict[str, Any]
    ) -> Any:
        """Coerce a provided input value to the declared type."""
        input_type = input_def.get("type", "string")
        enum_values = input_def.get("enum")

        if input_type == "number":
            try:
                value = float(value)
                if value == int(value):
                    value = int(value)
            except (ValueError, TypeError):
                msg = f"Input {name!r} expected a number, got {value!r}."
                raise ValueError(msg) from None
        elif input_type == "boolean":
            if isinstance(value, str):
                if value.lower() in ("true", "1", "yes"):
                    value = True
                elif value.lower() in ("false", "0", "no"):
                    value = False
                else:
                    msg = f"Input {name!r} expected a boolean, got {value!r}."
                    raise ValueError(msg)

        if enum_values is not None and value not in enum_values:
            msg = (
                f"Input {name!r} value {value!r} not in allowed "
                f"values: {enum_values}."
            )
            raise ValueError(msg)

        return value