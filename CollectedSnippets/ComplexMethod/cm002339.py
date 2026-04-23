def create_modules(
    modular_mapper: ModularFileMapper,
    file_path: str | None = None,
    package_name: str | None = "transformers",
) -> dict[str, cst.Module]:
    """Create all the new modules based on visiting the modular file. It replaces all classes as necessary."""
    files = defaultdict(dict)
    current_file_indices = defaultdict(lambda: 0)

    # For each class defined in modular, potentially replace the node and add it with its dependencies
    for class_name, node in modular_mapper.classes.items():
        nodes_to_add, file_type, new_imports = get_class_node_and_dependencies(modular_mapper, class_name, node, files)

        if package_name != "transformers":
            # New imports involve new files like configuration_xxx.py, etc
            # Those are imported with relative imports by default in the modeling file
            # Since relative imports are Transformers imports at this point in the code, convert them to absolute imports from the source library (e.g. optimum-habana)
            for key, new_import in new_imports.items():
                new_imports[key] = new_import.with_changes(
                    body=[
                        convert_relative_import_to_absolute(
                            import_node=new_import.body[0], file_path=file_path, package_name=package_name
                        )
                    ]
                )

        # Add the new potential new imports that we may need to the `modular_mapper` variable
        modular_mapper.imported_objects_per_file[file_type].update(new_imports.keys())
        modular_mapper.imports.extend(list(new_imports.values()))

        # Sort the nodes according to their relative order
        nodes_to_add = sorted(nodes_to_add.items(), key=lambda x: x[1][0])
        # Write all nodes to file
        for dependency, (_, node) in nodes_to_add:
            # This is used to keep certain variables at the beginning of the file
            try:
                # The -1000 is arbitrary -> just keep it bigger than the list
                idx = -1000 + VARIABLES_AT_THE_BEGINNING.index(dependency)
            except ValueError:
                idx = current_file_indices[file_type]
                current_file_indices[file_type] += 1
            files[file_type][dependency] = {"insert_idx": idx, "node": node}

    # Add the __all__ statement to files at the end
    for file_type, node in modular_mapper.all_all_to_add.items():
        idx = current_file_indices[file_type]
        files[file_type]["__all__"] = {"insert_idx": idx, "node": node}

    # Aggregate all the imports statements (we look for duplicates with the code_for_node, not the nodes themselves because
    # they are wrapped in SimpleStatementLine or If which could have different newlines, blanks etc)
    all_imports = modular_mapper.imports.copy()
    all_imports_code = {modular_mapper.python_module.code_for_node(node).strip() for node in all_imports}
    for file, mapper in modular_mapper.visited_modules.items():
        new_imports = [
            node for node in mapper.imports if mapper.python_module.code_for_node(node).strip() not in all_imports_code
        ]
        new_imports_code = {mapper.python_module.code_for_node(node).strip() for node in new_imports}
        all_imports.extend(new_imports)
        all_imports_code.update(new_imports_code)

    # Because `image_processing` file uses non-protected torchvision and torch imports, we need to duplicate the nodes
    # here instead of importing from `.image_processing_model`, which would crash if torchvision is not installed
    if "image_processing" in files and "image_processing_pil" in files:
        files = replace_unprotected_image_processing_imports(files, all_imports)

    # Find the correct imports, and write the new modules
    for file, body in files.items():
        new_body = [k[1]["node"] for k in sorted(body.items(), key=lambda x: x[1]["insert_idx"])]
        needed_imports = get_needed_imports(body, all_imports)

        if file == "image_processing_pil":
            needed_imports = protect_torch_imports_for_pil(needed_imports)

        if package_name != "transformers":
            # Convert all transformers relative imports to absolute ones
            for imp in needed_imports:
                if m.matches(imp, m.SimpleStatementLine(body=[m.ImportFrom()])):
                    imp.body[0] = convert_relative_import_to_absolute(
                        import_node=imp.body[0], file_path=file_path, package_name="transformers"
                    )

        full_module = needed_imports + new_body
        new_module = cst.Module(body=full_module, header=modular_mapper.python_module.header)
        files[file] = new_module

    return files