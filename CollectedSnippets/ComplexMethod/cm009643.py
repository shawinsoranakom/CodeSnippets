def _dereference_refs_helper(
    obj: Any,
    full_schema: dict[str, Any],
    processed_refs: set[str] | None,
    skip_keys: Sequence[str],
    *,
    shallow_refs: bool,
) -> Any:
    """Dereference JSON Schema $ref objects, handling both pure and mixed references.

    This function processes JSON Schema objects containing $ref properties by resolving
    the references and merging any additional properties. It handles:

    - Pure `$ref` objects: `{"$ref": "#/path/to/definition"}`
    - Mixed `$ref` objects: `{"$ref": "#/path", "title": "Custom Title", ...}`
    - Circular references by breaking cycles and preserving non-ref properties

    Args:
        obj: The object to process (can be dict, list, or primitive)
        full_schema: The complete schema containing all definitions
        processed_refs: Set tracking currently processing refs (for cycle detection)
        skip_keys: Keys under which to skip recursion
        shallow_refs: If `True`, only break cycles; if `False`, deep-inline all refs

    Returns:
        The object with `$ref` properties resolved and merged with other properties.
    """
    if processed_refs is None:
        processed_refs = set()

    # Case 1: Object contains a $ref property (pure or mixed with additional properties)
    if isinstance(obj, dict) and "$ref" in obj:
        ref_path = obj["$ref"]
        additional_properties = {
            key: value for key, value in obj.items() if key != "$ref"
        }

        # Detect circular reference: if we're already processing this $ref,
        # return only the additional properties to break the cycle
        if ref_path in processed_refs:
            return _process_dict_properties(
                additional_properties,
                full_schema,
                processed_refs,
                skip_keys,
                shallow_refs=shallow_refs,
            )

        # Mark this reference as being processed (for cycle detection)
        processed_refs.add(ref_path)

        # Fetch and recursively resolve the referenced object
        referenced_object = deepcopy(_retrieve_ref(ref_path, full_schema))
        resolved_reference = _dereference_refs_helper(
            referenced_object,
            full_schema,
            processed_refs,
            skip_keys,
            shallow_refs=shallow_refs,
        )

        # Clean up: remove from processing set before returning
        processed_refs.remove(ref_path)

        # Pure $ref case: no additional properties, return resolved reference directly
        if not additional_properties:
            return resolved_reference

        # Mixed $ref case: merge resolved reference with additional properties
        # Additional properties take precedence over resolved properties
        merged_result = {}
        if isinstance(resolved_reference, dict):
            merged_result.update(resolved_reference)

        # Process additional properties and merge them (they override resolved ones)
        processed_additional = _process_dict_properties(
            additional_properties,
            full_schema,
            processed_refs,
            skip_keys,
            shallow_refs=shallow_refs,
        )
        merged_result.update(processed_additional)

        return merged_result

    # Case 2: Regular dictionary without $ref - process all properties
    if isinstance(obj, dict):
        return _process_dict_properties(
            obj, full_schema, processed_refs, skip_keys, shallow_refs=shallow_refs
        )

    # Case 3: List - recursively process each item
    if isinstance(obj, list):
        return [
            _dereference_refs_helper(
                item, full_schema, processed_refs, skip_keys, shallow_refs=shallow_refs
            )
            for item in obj
        ]

    # Case 4: Primitive value (string, number, boolean, null) - return unchanged
    return obj