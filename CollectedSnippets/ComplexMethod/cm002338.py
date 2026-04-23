def get_class_node_and_dependencies(
    modular_mapper: ModularFileMapper, class_name: str, node: cst.CSTNode, files: dict[str, dict]
) -> tuple[dict, str, dict]:
    """Return a single class node (and all its dependency nodes), to be added to the `files`. It creates the new
    class node based on the inherited classes if needed. Also returns any new imports of a new class defined in
    the modular that we nay need.
    """
    # An exception was already raised if this has len > 1
    model_specific_bases = [
        k.value.value for k in node.bases if k.value.value in modular_mapper.model_specific_imported_objects
    ]
    super_class = model_specific_bases[0] if len(model_specific_bases) == 1 else None

    file_type = find_file_type(class_name, modular_mapper.model_name)
    file_to_update = files[file_type]
    model_name = modular_mapper.model_name

    # This is used to avoid adding objects to the dependencies graph if they will be imported already
    imported_objects = modular_mapper.imported_objects_per_file[file_type]

    # We need to replace the class node with the transformers (modeling file) super class node
    if super_class is not None:
        super_file_name = modular_mapper.model_specific_imported_objects[super_class]

        # Get the mapper corresponding to the inherited class
        mapper = modular_mapper.visited_modules[super_file_name]
        # Rename the super class according to the exact same rule we used when renaming the whole module
        renamer = modular_mapper.renamers[super_file_name]
        renamed_super_class = preserve_case_replace(super_class, renamer.patterns, renamer.cased_new_name)

        # Create the new class node
        updated_node = replace_class_node(mapper, node, renamed_super_class, super_class)

        # Grab all immediate dependencies of the new node
        new_node_dependencies = augmented_dependencies_for_class_node(updated_node, mapper, imported_objects)

        # At this point, if any class dependency is found, but belongs to another file, it means that we need to remove
        # it from the dependencies, and add a new import of it instead
        new_node_dependencies, new_imports = check_dependencies_and_create_import_node(
            file_type, new_node_dependencies, mapper, model_name
        )

        # Remove all classes explicitly defined in modular from the dependencies. Otherwise, if a class is referenced
        # before its new modular definition, it may be wrongly imported from elsewhere as a dependency if it matches
        # another class from a modeling file after renaming, even though it would be added after anyway (leading to duplicates)
        new_node_dependencies -= set(modular_mapper.classes.keys())

        # The node was modified -> look for all recursive dependencies of the new node
        all_dependencies_to_add = find_all_dependencies(
            dependency_mapping=mapper.class_dependency_mapping,
            initial_dependencies=new_node_dependencies,
            initial_checked_dependencies=set(file_to_update.keys()),
        )

        relative_dependency_order = mapper.compute_relative_order(all_dependencies_to_add)
        nodes_to_add = {
            dep: (relative_dependency_order[dep], mapper.global_nodes[dep]) for dep in all_dependencies_to_add
        }

    # No transformers (modeling file) super class, just check functions and assignments dependencies
    else:
        updated_node = node
        # The node was NOT modified -> no need to look recursively for other class dependencies. Indeed, even if they are not
        # already defined (which would mean a weird order of the code in the modular...), they will be in the future
        all_dependencies_to_add = augmented_dependencies_for_class_node(updated_node, modular_mapper, imported_objects)

        # At this point, if any class dependency is found, but belongs to another file, it means that we need to remove
        # it from the dependencies, and add a new import of it instead
        all_dependencies_to_add, new_imports = check_dependencies_and_create_import_node(
            file_type, all_dependencies_to_add, modular_mapper, model_name
        )

        relative_dependency_order = modular_mapper.compute_relative_order(all_dependencies_to_add)
        nodes_to_add = {
            dep: (relative_dependency_order[dep], modular_mapper.global_nodes[dep])
            for dep in all_dependencies_to_add
            if dep not in file_to_update
        }

    # Add the class node itself to the nodes to add
    class_idx = max(relative_dependency_order.values()) + 1 if len(relative_dependency_order) > 0 else 0
    nodes_to_add[class_name] = (class_idx, updated_node)

    return nodes_to_add, file_type, new_imports