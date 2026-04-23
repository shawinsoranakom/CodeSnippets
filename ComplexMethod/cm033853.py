def _get_module_metadata(module: ast.Module) -> ModuleMetadata:
    # experimental module metadata; off by default
    if not C.config.get_config_value('_MODULE_METADATA'):
        return _DEFAULT_LEGACY_METADATA

    metadata_nodes: list[ast.Assign] = []

    for node in module.body:
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1:
                target = node.targets[0]

                if isinstance(target, ast.Name):
                    if target.id == 'METADATA':
                        metadata_nodes.append(node)

    if not metadata_nodes:
        return _DEFAULT_LEGACY_METADATA

    if len(metadata_nodes) > 1:
        raise ValueError('Module METADATA must defined only once.')

    metadata_node = metadata_nodes[0]

    if not isinstance(metadata_node.value, ast.Constant):
        raise TypeError(f'Module METADATA node must be {ast.Constant} not {type(metadata_node)}.')

    unparsed_metadata = metadata_node.value.value

    if not isinstance(unparsed_metadata, str):
        raise TypeError(f'Module METADATA must be {str} not {type(unparsed_metadata)}.')

    try:
        parsed_metadata = yaml_load(unparsed_metadata)
    except Exception as ex:
        raise ValueError('Module METADATA must be valid YAML.') from ex

    if not isinstance(parsed_metadata, dict):
        raise TypeError(f'Module METADATA must parse to {dict} not {type(parsed_metadata)}.')

    schema_version = parsed_metadata.pop('schema_version', None)

    if not (metadata_type := metadata_versions.get(schema_version)):
        raise ValueError(f'Module METADATA schema_version {schema_version} is unknown.')

    try:
        metadata = metadata_type(**parsed_metadata)  # type: ignore
    except Exception as ex:
        raise ValueError('Module METADATA is invalid.') from ex

    return metadata