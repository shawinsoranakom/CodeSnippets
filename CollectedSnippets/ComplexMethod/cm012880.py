def prepare(
    model: GraphModule,
    qconfig_mapping: QConfigMapping | dict[str, Any],
    is_qat: bool,
    node_name_to_scope: dict[str, tuple[str, type]],
    example_inputs: tuple[Any, ...],
    prepare_custom_config: PrepareCustomConfig | dict[str, Any] | None = None,
    _equalization_config: QConfigMapping | dict[str, Any] | None = None,
    backend_config: BackendConfig | dict[str, Any] | None = None,
    is_standalone_module: bool = False,
) -> GraphModule:
    """standalone_module means it a submodule that is not inlined in
    parent module, and will be quantized separately as one unit.

    How the standalone module is observed is specified by `input_quantized_idxs` and
    `output_quantized_idxs` in the prepare_custom_config for the standalone module
    Args:
        node_name_to_scope: mapping from node name to the scope of the module which contains the node.
        The scope is a tuple of fully qualified path of the module and the type of the module
    Returns:
        model(GraphModule): prepared standalone module
        attributes related to standalone module
        in model.meta["_observed_graph_module_attrs"]:
            is_observed_standalone_module (bool): boolean value that shows whether the
            current model is a observed standalone module or not
            standalone_module_input_quantized_idxs(List[Int]): a list of
                indexes for the graph input that is expected to be quantized,
                same as input_quantized_idxs configuration provided
                for the standalone module
            standalone_module_output_quantized_idxs(List[Int]): a list of
                indices for the graph output that is quantized
                same as input_quantized_idxs configuration provided
                for the standalone module
    """
    if prepare_custom_config is None:
        prepare_custom_config = PrepareCustomConfig()
    if _equalization_config is None:
        _equalization_config = QConfigMapping()

    if isinstance(qconfig_mapping, dict):
        warnings.warn(
            "Passing a QConfig dictionary to prepare is deprecated and will not be supported "
            "in a future version. Please pass in a QConfigMapping instead.",
            FutureWarning,
            stacklevel=2,
        )
        qconfig_mapping = QConfigMapping.from_dict(qconfig_mapping)

    if isinstance(_equalization_config, dict):
        warnings.warn(
            "Passing a QConfig dictionary to prepare for equalization is deprecated and will not "
            "be supported in a future version. Please pass in a QConfigMapping instead.",
            FutureWarning,
            stacklevel=2,
        )
        _equalization_config = QConfigMapping.from_dict(_equalization_config)

    if isinstance(prepare_custom_config, dict):
        warnings.warn(
            "Passing a prepare_custom_config_dict to prepare is deprecated and will not be supported "
            "in a future version. Please pass in a PrepareCustomConfig instead.",
            FutureWarning,
            stacklevel=2,
        )
        prepare_custom_config = PrepareCustomConfig.from_dict(prepare_custom_config)

    if isinstance(backend_config, dict):
        warnings.warn(
            "Passing a backend_config_dict to prepare is deprecated and will not be supported "
            "in a future version. Please pass in a BackendConfig instead.",
            FutureWarning,
            stacklevel=2,
        )
        backend_config = BackendConfig.from_dict(backend_config)

    if not isinstance(qconfig_mapping, QConfigMapping):
        raise AssertionError("qconfig_mapping must be a QConfigMapping")
    if not isinstance(_equalization_config, QConfigMapping):
        raise AssertionError("_equalization_config must be a QConfigMapping")
    qconfig_mapping = copy.deepcopy(qconfig_mapping)
    _equalization_config = copy.deepcopy(_equalization_config)

    # mapping from a tuple of nodes in reverse order to uninitialized
    #   QuantizeHandler subclass. For example,
    # {
    #   # match a single node
    #   (<class 'torch.nn.modules.conv.Conv3d'>:
    #     <class 'torch.ao.quantization.fx.quantize.ConvRelu'>),
    #   # match multiple nodes in reverse order
    #   ((<function relu at 0x7f766a7360d0>, <built-in function add>):
    #     <class 'torch.ao.quantization.fx.quantize.Add'>),
    # }

    pattern_to_quantize_handler: dict[Pattern, QuantizeHandler] = {}
    if backend_config is None:
        backend_config = get_native_backend_config()
    pattern_to_quantize_handler = _get_pattern_to_quantize_handlers(backend_config)
    pattern_to_quantize_handler = _sorted_patterns_dict(pattern_to_quantize_handler)

    root_node_getter_mapping = get_fusion_pattern_to_root_node_getter(backend_config)

    # pyrefly: ignore [bad-argument-type]
    _update_qconfig_for_fusion(model, qconfig_mapping)
    # pyrefly: ignore [bad-argument-type]
    _update_qconfig_for_fusion(model, _equalization_config)
    # pyrefly: ignore [bad-argument-type]
    flattened_qconfig_dict = _get_flattened_qconfig_dict(qconfig_mapping)
    # TODO: support regex as well
    propagate_qconfig_(model, flattened_qconfig_dict, prepare_custom_config.to_dict())

    if is_qat:
        module_to_qat_module = get_module_to_qat_module(backend_config)
        _qat_swap_modules(model, module_to_qat_module)
        # pyrefly: ignore [bad-argument-type]
        _update_qconfig_for_qat(qconfig_mapping, backend_config)

    # mapping from fully qualified module name to module instance
    # for example,
    # {
    #   '': Model(...),
    #   'linear': Linear(...),
    #   'linear.weight_fake_quant': PerChannelMinMaxObserver(...),
    # }
    named_modules = dict(model.named_modules(remove_duplicate=False))

    # fill node_name_to_qconfig, a map from node name to qconfig, used in _find_matches
    equalization_node_name_to_qconfig = _generate_node_name_to_qconfig(
        model,
        named_modules,
        model.graph,
        # pyrefly: ignore [bad-argument-type]
        _equalization_config,
        node_name_to_scope,
    )
    node_name_to_qconfig = _generate_node_name_to_qconfig(
        model,
        named_modules,
        model.graph,
        # pyrefly: ignore [bad-argument-type]
        qconfig_mapping,
        node_name_to_scope,
    )

    # match the patterns that will get quantized
    standalone_module_names = list(prepare_custom_config.standalone_module_names.keys())
    standalone_module_classes = list(
        prepare_custom_config.standalone_module_classes.keys()
    )

    custom_module_classes = get_custom_module_class_keys(
        prepare_custom_config.float_to_observed_mapping
    )
    matches_without_qconfig = _find_matches(
        model.graph,
        named_modules,
        pattern_to_quantize_handler,
        root_node_getter_mapping,
        standalone_module_names,
        standalone_module_classes,
        custom_module_classes,
    )

    # map qconfig instances to matches
    node_name_to_match_result_with_qconfig = {}
    for node_name, match_without_qconfig in matches_without_qconfig.items():
        match_with_qconfig = (*match_without_qconfig, node_name_to_qconfig[node_name])
        node_name_to_match_result_with_qconfig[node_name] = match_with_qconfig

    _run_prepare_fx_on_standalone_modules(
        model,
        is_qat,
        named_modules,
        node_name_to_match_result_with_qconfig,
        prepare_custom_config,
        backend_config,
    )

    # record names for the set of observed node, so that in convert step
    # we know whether we need to convert a floating point module to reference
    # quantized module or not
    observed_node_names: set[str] = set()

    result_node = insert_observers_for_model(
        model,
        node_name_to_match_result_with_qconfig,
        node_name_to_qconfig,
        prepare_custom_config,
        equalization_node_name_to_qconfig,
        backend_config,
        observed_node_names,
        is_qat,
    )
    model = GraphModule(model, model.graph)

    _save_state(
        model,
        node_name_to_qconfig,
        node_name_to_scope,
        prepare_custom_config,
        equalization_node_name_to_qconfig,
        # pyrefly: ignore [bad-argument-type]
        qconfig_mapping,
        is_qat,
        observed_node_names,
    )

    if is_standalone_module:
        if result_node is None:
            raise AssertionError("result_node must not be None for standalone modules")
        if not isinstance(result_node.args[0], Node):
            raise AssertionError(
                "standalone module only supports returning simple value currently (not tuple, dict etc.)"
            )
        # these inputs are observed in parent
        # converting List[int] to Tensor since module attribute is
        # Union[Tensor, Module]
        input_quantized_idxs: list[int] = prepare_custom_config.input_quantized_indexes
        output_quantized_idxs: list[int] = (
            prepare_custom_config.output_quantized_indexes
        )
        observed_graph_module_attrs = model.meta["_observed_graph_module_attrs"]
        # inplace modification
        observed_graph_module_attrs.is_observed_standalone_module = True
        observed_graph_module_attrs.standalone_module_input_quantized_idxs = (
            input_quantized_idxs
        )
        observed_graph_module_attrs.standalone_module_output_quantized_idxs = (
            output_quantized_idxs
        )
    return model