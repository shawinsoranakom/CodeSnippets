def _is_pattern_dtype_config_and_qconfig_supported_by_backend(
    pattern: Pattern | None,
    matched_node_pattern: list[Node] | None,
    qconfig: QConfigAny,
    backend_config: BackendConfig,
) -> bool:
    """Check if the dtype configuration of a pattern is supported by
    the backend or not, and whether the qconfig satisfies constraints
    specified in the corresponding dtype config.
    """
    if backend_config is None or pattern is None:
        return True
    if matched_node_pattern is None or len(matched_node_pattern) < 1:
        raise AssertionError("matched_node_pattern must be non-empty")
    pattern_to_dtype_configs = get_pattern_to_dtype_configs(backend_config)
    dtype_configs: list[DTypeConfig] = pattern_to_dtype_configs.get(pattern, [])
    pattern_to_root_node_getter = get_fusion_pattern_to_root_node_getter(backend_config)

    root_node_getter = pattern_to_root_node_getter.get(
        pattern, _default_root_node_getter
    )
    root_node = root_node_getter(matched_node_pattern)
    input_node = root_node
    output_node = matched_node_pattern[0]
    for dtype_config in dtype_configs:
        # check if arg dtype are supported
        supported = True
        for arg in list(input_node.args) + list(input_node.kwargs.values()):
            supported = supported and _is_input_arg_dtype_supported_by_backend(
                arg, input_node, qconfig, dtype_config, backend_config
            )
        # check if output dtype is supported
        supported = supported and _is_output_dtype_supported_by_backend(
            output_node, qconfig, dtype_config
        )
        if supported:
            return True
    return False