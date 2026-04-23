def _adapt_to_schema(parsed: Any, prop_schema: dict[str, Any] | None) -> Any:
    """Adapt a parsed file value to better fit the target schema type.

    When the parser returns a natural type (e.g. dict from YAML, list from CSV)
    that doesn't match the block's expected type, this function converts it to
    a more useful representation instead of relying on pydantic's generic
    coercion (which can produce awkward results like flattened dicts → lists).

    Returns *parsed* unchanged when no adaptation is needed.
    """
    if prop_schema is None:
        return parsed

    target_type = prop_schema.get("type")

    # Dict → array: delegate to helper.
    if isinstance(parsed, dict) and target_type == "array":
        return _adapt_dict_to_array(parsed, prop_schema)

    # List → object: delegate to helper (raises for non-tabular lists).
    if isinstance(parsed, list) and target_type == "object":
        return _adapt_list_to_object(parsed)

    # Tabular list → Any (no type): convert to list of dicts.
    # Blocks like FindInDictionaryBlock have `input: Any` which produces
    # a schema with no "type" key.  Tabular [[header],[rows]] is unusable
    # for key lookup, but [{col: val}, ...] works with FindInDict's
    # list-of-dicts branch (line 195-199 in data_manipulation.py).
    if isinstance(parsed, list) and target_type is None and _is_tabular(parsed):
        return _tabular_to_list_of_dicts(parsed)

    return parsed