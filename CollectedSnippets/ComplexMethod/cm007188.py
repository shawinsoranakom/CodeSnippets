def _handle_dict_field(self, field_name: str, val: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Handle dictionary field type."""
        match val:
            case list():
                # Convert list of {"key": k, "value": v} pairs to a flat dict.
                # e.g. [{"key": "h1", "value": "v1"}, {"key": "h2", "value": "v2"}] -> {"h1": "v1", "h2": "v2"}
                if val and all(isinstance(item, dict) and "key" in item and "value" in item for item in val):
                    params[field_name] = {item["key"]: item["value"] for item in val}
                else:
                    # Merge generic list of dicts into a single dict.
                    # e.g. [{"a": 1}, {"b": 2}] -> {"a": 1, "b": 2}
                    params[field_name] = {k: v for item in val for k, v in item.items()}
            case dict():
                params[field_name] = val
            case _:
                logger.warning(
                    "Unexpected type %s for dict field '%s'; expected list or dict, got %r",
                    type(val).__name__,
                    field_name,
                    val,
                )
                params[field_name] = val
        return params