def replace_unprotected_image_processing_imports(files: dict, all_imports: list) -> dict:
    """
    Because `image_processing` file uses non-protected torchvision and torch imports, we need to duplicate the nodes
    inside `image_processing_pil` instead of importing them directly from `.image_processing_xxx`, which would crash if
    torchvision is not installed.
    """
    if not ("image_processing" in files and "image_processing_pil" in files):
        return files

    body = files["image_processing_pil"]
    needed_imports = get_needed_imports(body, all_imports)
    import_from_image_processing = None
    for import_node in needed_imports:
        if isinstance(import_node, cst.SimpleStatementLine) and isinstance(import_node.body[0], cst.ImportFrom):
            import_node = import_node.body[0]
            full_name = get_full_attribute_name(import_node.module)
            if re.search(r"^image_processing_(?!(?:backends)|(?:utils))", full_name):
                import_from_image_processing = import_node
                break

    if import_from_image_processing is None:
        return files

    imported_objects = [x.name.value for x in import_from_image_processing.names]
    nodes_to_add = {name: files["image_processing"][name] for name in imported_objects}
    # Update the position inside the final file
    for name, node_structure in nodes_to_add.items():
        node_with_same_index = next(
            v["node"] for v in body.values() if v["insert_idx"] == node_structure["insert_idx"]
        )
        # Insert the new node before the corresponding node if the corresponding node is a class or function
        if isinstance(node_with_same_index, (cst.ClassDef, cst.FunctionDef)):
            nodes_to_add[name]["insert_idx"] -= 0.5
        # Otherwise, after it
        else:
            nodes_to_add[name]["insert_idx"] += 0.5
    # Add the nodes inside the body of `image_processing_pil`
    body.update(nodes_to_add)
    return files