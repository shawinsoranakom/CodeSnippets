def _normalize_arguments_for_mcp(
    arguments: dict[str, Any], arg_schema: type[BaseModel], tool_name: str
) -> dict[str, Any]:
    """Normalize tool arguments for MCP: try-convert when value type != schema expected type.

    Uses schema from MCP server (no guessing). On conversion failure, raises
    ValueError with clear user-facing message.
    """
    result: dict[str, Any] = {}
    schema_field_names = set(arg_schema.model_fields.keys())
    for field_name, model_field in arg_schema.model_fields.items():
        value = arguments.get(field_name)
        if value is None:
            if not (model_field.is_required() or field_name in arguments):
                continue
            expected = _resolve_expected_type(model_field.annotation)
            if expected in (list, dict, str) and model_field.is_required():
                result[field_name] = [] if expected is list else ({} if expected is dict else "")
            elif expected in (list, dict, str) and _annotation_accepts_none(model_field.annotation):
                result[field_name] = None
            else:
                result[field_name] = value
            continue
        expected = _resolve_expected_type(model_field.annotation)
        if expected is None:
            # Nested Pydantic model (object with properties): UI/API often sends as JSON string
            if _is_pydantic_model_type(model_field.annotation) and isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError as e:
                    msg = (
                        f"Tool '{tool_name}': Parameter '{field_name}' expects object "
                        f"but received invalid JSON string {value!r}; {e}"
                    )
                    raise ValueError(msg) from e
                if not isinstance(parsed, dict):
                    msg = (
                        f"Tool '{tool_name}': Parameter '{field_name}' expects object "
                        f"but JSON parsed to {type(parsed).__name__}."
                    )
                    raise ValueError(msg)
                result[field_name] = parsed
            else:
                result[field_name] = value
            continue
        if expected is str:
            result[field_name] = value
            continue
        result[field_name] = _try_convert_value(value, expected, field_name, tool_name)
    # Preserve extra keys so Pydantic validation can report them
    result.update({k: v for k, v in arguments.items() if k not in schema_field_names})
    return result