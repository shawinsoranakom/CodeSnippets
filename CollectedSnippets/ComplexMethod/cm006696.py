def validate_formatter(cls, value):
        if value in {"boolean", "bool"}:
            value = FormatterType.boolean
        if value in {"integer", "int", "float"}:
            value = FormatterType.number
        if value in {"str", "string"}:
            value = FormatterType.text
        if value == "dict":
            value = FormatterType.json
        if value == "date":
            value = FormatterType.date
        if isinstance(value, str):
            return FormatterType(value)
        if isinstance(value, FormatterType):
            return value
        msg = f"Invalid formatter type: {value}. Valid types are: {FormatterType}"
        raise ValueError(msg)