def _resolve_schema(
    schema_hints: dict[type, dict[str, Any]],
    schema_name: str,
    omit_flag: str | None = None,
) -> type:
    """Resolve schema by merging schemas and optionally respecting `OmitFromSchema` annotations.

    Args:
        schema_hints: Resolved schema annotations to merge
        schema_name: Name for the generated `TypedDict`
        omit_flag: If specified, omit fields with this flag set (`'input'` or
            `'output'`)

    Returns:
        Merged schema as `TypedDict`
    """
    all_annotations = {}

    for hints in schema_hints.values():
        for field_name, field_type in hints.items():
            should_omit = False

            if omit_flag:
                metadata = _extract_metadata(field_type)
                for meta in metadata:
                    if isinstance(meta, OmitFromSchema) and getattr(meta, omit_flag) is True:
                        should_omit = True
                        break

            if not should_omit:
                all_annotations[field_name] = field_type

    return TypedDict(schema_name, all_annotations)