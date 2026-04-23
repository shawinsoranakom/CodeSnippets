def _find_typed_dict_classes(source: str, tree: ast.Module | None = None) -> list[dict]:
    """
    Find all custom TypedDict kwargs classes in the source.

    Returns:
        List of dicts with TypedDict info: name, line, fields, all_fields, field_types, docstring info
        - fields: fields that need custom documentation (not in standard args, not nested TypedDicts)
        - all_fields: all fields including those in standard args (for redundancy checking)
    """
    if tree is None:
        tree = ast.parse(source)

    # Get standard args that are already documented in source classes
    standard_args = set()
    try:
        standard_args.update(get_args_doc_from_source([ModelArgs, ImageProcessorArgs, ProcessorArgs]).keys())
    except Exception as e:
        logger.debug(f"Could not get standard args from source: {e}")

    # Collect TypedDict class names and nodes (TypedDicts are always top-level)
    typed_dict_names = set()
    typed_dict_nodes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and ("TypedDict" in base.id or "Kwargs" in base.id):
                    typed_dict_names.add(node.name)
                    typed_dict_nodes.append(node)
                    break

    typed_dicts = []

    # Check each TypedDict class
    for node in typed_dict_nodes:
        # Skip standard kwargs classes
        if node.name in ["TextKwargs", "ImagesKwargs", "VideosKwargs", "AudioKwargs", "ProcessingKwargs"]:
            continue

        # Extract fields and their types (in declaration order)
        fields = []  # Fields that need custom documentation
        all_fields = []  # All fields including those in standard args
        field_types = {}
        for class_item in node.body:
            if isinstance(class_item, ast.AnnAssign) and isinstance(class_item.target, ast.Name):
                field_name = class_item.target.id
                if not field_name.startswith("_"):
                    # Extract type and check if it's a nested TypedDict
                    if class_item.annotation:
                        type_name = _extract_type_name(class_item.annotation)
                        if type_name:
                            field_types[field_name] = type_name
                            # Skip nested TypedDicts
                            if type_name in typed_dict_names or type_name.endswith("Kwargs"):
                                continue
                    # Track all fields for redundancy checking
                    all_fields.append(field_name)
                    # Only add to fields if not in standard args (needs custom documentation)
                    if field_name not in standard_args:
                        fields.append(field_name)

        # Skip if no fields at all (including standard args)
        if not all_fields:
            continue

        # Extract docstring info
        docstring = None
        docstring_start_line = None
        docstring_end_line = None
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            docstring = node.body[0].value.value
            docstring_start_line = node.body[0].lineno
            docstring_end_line = node.body[0].end_lineno

        typed_dicts.append(
            {
                "name": node.name,
                "line": node.lineno,
                "fields": fields,
                "all_fields": all_fields,
                "field_types": field_types,
                "docstring": docstring,
                "docstring_start_line": docstring_start_line,
                "docstring_end_line": docstring_end_line,
            }
        )

    return typed_dicts