def extract_block_doc(block_cls: type) -> BlockDoc:
    """Extract documentation data from a block class."""
    block = block_cls.create()

    # Get source file
    try:
        source_file = inspect.getfile(block_cls)
        # Make relative to blocks directory
        blocks_dir = Path(source_file).parent
        while blocks_dir.name != "blocks" and blocks_dir.parent != blocks_dir:
            blocks_dir = blocks_dir.parent
        source_file = str(Path(source_file).relative_to(blocks_dir.parent))
    except (TypeError, ValueError):
        source_file = "unknown"

    # Extract input fields
    input_schema = block.input_schema.jsonschema()
    input_properties = safe_get(input_schema, "properties", {})
    if not isinstance(input_properties, dict):
        input_properties = {}
    required_raw = safe_get(input_schema, "required", [])
    # Handle edge cases where required might not be a list
    if isinstance(required_raw, (list, set, tuple)):
        required_inputs = set(required_raw)
    else:
        required_inputs = set()

    inputs = []
    for field_name, field_schema in input_properties.items():
        if not isinstance(field_schema, dict):
            continue
        # Skip credentials fields in docs (they're auto-handled)
        if "credentials" in field_name.lower():
            continue

        inputs.append(
            FieldDoc(
                name=field_name,
                description=safe_get(field_schema, "description", ""),
                type_str=type_to_readable(field_schema),
                required=field_name in required_inputs,
                default=safe_get(field_schema, "default"),
                advanced=safe_get(field_schema, "advanced", False) or False,
                hidden=safe_get(field_schema, "hidden", False) or False,
                placeholder=safe_get(field_schema, "placeholder"),
            )
        )

    # Extract output fields
    output_schema = block.output_schema.jsonschema()
    output_properties = safe_get(output_schema, "properties", {})
    if not isinstance(output_properties, dict):
        output_properties = {}

    outputs = []
    for field_name, field_schema in output_properties.items():
        if not isinstance(field_schema, dict):
            continue
        outputs.append(
            FieldDoc(
                name=field_name,
                description=safe_get(field_schema, "description", ""),
                type_str=type_to_readable(field_schema),
                required=True,  # Outputs are always produced
                hidden=safe_get(field_schema, "hidden", False) or False,
            )
        )

    # Get category info (sort for deterministic ordering since it's a set)
    categories = []
    category_descriptions = {}
    for cat in sorted(block.categories, key=lambda c: c.name):
        categories.append(cat.name)
        category_descriptions[cat.name] = cat.value

    # Get contributors
    contributors = []
    for contrib in block.contributors:
        contributors.append(contrib.name if hasattr(contrib, "name") else str(contrib))

    return BlockDoc(
        id=block.id,
        name=class_name_to_display_name(block.name),
        class_name=block.name,
        description=block.description,
        categories=categories,
        category_descriptions=category_descriptions,
        inputs=inputs,
        outputs=outputs,
        block_type=block.block_type.value,
        source_file=source_file,
        contributors=contributors,
    )
