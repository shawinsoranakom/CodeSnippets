def convert(
    model: GraphModule,
    is_reference: bool = False,
    convert_custom_config: ConvertCustomConfig | dict[str, Any] | None = None,
    is_standalone_module: bool = False,
    _remove_qconfig_flag: bool = True,
    qconfig_mapping: QConfigMapping | dict[str, Any] | None = None,
    backend_config: BackendConfig | dict[str, Any] | None = None,
    is_decomposed: bool = False,
    keep_original_weights: bool = False,
) -> GraphModule:
    """
    We will convert an observed model (a module with observer calls) to a reference
    quantized model, the rule is simple:
    1. for each observer module call in the graph, we'll convert it to calls to
       quantize and dequantize functions based on the observer instance
    2. for weighted operations like linear/conv, we need to convert them to reference
       quantized module, this requires us to know whether the dtype configured for the
       weight is supported in the backend, this is done in prepare step and the result
       is stored in observed_node_names, we can decide whether we need to swap the
       module based on this set

    Args:
       * `is_standalone_module`: when this flag is True, it means we are quantizing
       a submodule that is not inlined in parent module, and will be quantized
       separately as one unit.

       * `is_decomposed`: a boolean flag to indicate whether we want to use the
        quantize operator for decomposed quantized tensor
        (torch.ops.quantized_decomposed.quantize_per_tensor) or default/standalone
        quantized tensor (torch.quantize_per_tensor)

    Returns:
         a quantized standalone module, whether input/output is quantized is
         specified by prepare_custom_config, with
         input_quantized_idxs, output_quantized_idxs, please
         see docs for :func:`~torch.ao.quantization.prepare_fx` for details
    """
    if convert_custom_config is None:
        convert_custom_config = ConvertCustomConfig()

    if isinstance(convert_custom_config, dict):
        warnings.warn(
            "Passing a convert_custom_config_dict to convert is deprecated and will not be supported "
            "in a future version. Please pass in a ConvertCustomConfig instead.",
            FutureWarning,
            stacklevel=2,
        )
        convert_custom_config = ConvertCustomConfig.from_dict(convert_custom_config)

    if isinstance(qconfig_mapping, dict):
        warnings.warn(
            "Passing a QConfig dictionary to convert is deprecated and will not be supported "
            "in a future version. Please pass in a QConfigMapping instead.",
            FutureWarning,
            stacklevel=2,
        )
        qconfig_mapping = (
            QConfigMapping.from_dict(qconfig_mapping) if qconfig_mapping else None
        )
    qconfig_mapping = copy.deepcopy(qconfig_mapping)
    if not (qconfig_mapping is None or isinstance(qconfig_mapping, QConfigMapping)):
        raise AssertionError("qconfig_mapping must be None or a QConfigMapping")

    if isinstance(backend_config, dict):
        warnings.warn(
            "Passing a backend_config_dict to prepare is deprecated and will not be supported "
            "in a future version. Please pass in a BackendConfig instead.",
            FutureWarning,
            stacklevel=2,
        )
        backend_config = BackendConfig.from_dict(backend_config)

    if backend_config is None:
        backend_config = get_native_backend_config()

    if not _is_observed_module(model):
        raise AssertionError("incoming model must be produced by prepare_fx")
    observed_graph_module_attrs = model.meta["_observed_graph_module_attrs"]
    node_name_to_scope: dict[str, tuple[str, type]] = (
        observed_graph_module_attrs.node_name_to_scope
    )
    prepare_custom_config: PrepareCustomConfig = (
        observed_graph_module_attrs.prepare_custom_config
    )
    observed_node_names: set[str] = observed_graph_module_attrs.observed_node_names
    node_name_to_qconfig: dict[str, QConfigAny] = (
        observed_graph_module_attrs.node_name_to_qconfig
    )  # type: ignore[assignment]

    # mapping from fully qualified module name to module instance
    # for example,
    # {
    #   '': Model(...),
    #   'linear': Linear(...),
    #   'linear.weight_fake_quant': PerChannelMinMaxObserver(...),
    # }
    # We use remove_duplicate=False here because torch.cat uses
    # the same activation_post_process module instance but different names
    modules = dict(model.named_modules(remove_duplicate=False))

    # TODO refactor this code once we update the prepare logic to have additional information on
    # which graph nodes have been observed and share that with convert to decide which observers to ignore.
    if qconfig_mapping:
        prepare_qconfig_mapping: QConfigMapping = (
            observed_graph_module_attrs.qconfig_mapping
        )  # type: ignore[assignment]
        modules_copy = copy.deepcopy(modules)

        if observed_graph_module_attrs.is_qat:
            _update_qconfig_for_qat(qconfig_mapping, backend_config)
        _update_qconfig_for_fusion(model, qconfig_mapping)

        _compare_prepare_convert_qconfig_mappings(
            prepare_qconfig_mapping, qconfig_mapping
        )  # type: ignore[arg-type]
        convert_node_name_to_qconfig = _generate_node_name_to_qconfig(
            model, modules_copy, model.graph, qconfig_mapping, node_name_to_scope
        )
        # check the convert_node_name_to_qconfig generated and ensure that
        # all the values either match what was set in prepare node_name_to_qconfig
        # or are set to None in the convert_node_name_to_qconfig.
        for k, v in node_name_to_qconfig.items():
            if k not in convert_node_name_to_qconfig:
                raise AssertionError(
                    f"Expected key {k} in convert node_name_to_qconfig"
                )
            if convert_node_name_to_qconfig[k] is not None:
                if not qconfig_equals(v, convert_node_name_to_qconfig[k]):
                    raise AssertionError(
                        f"Expected k {k} to have the same value in prepare and convert QConfigMappings, "
                        f"but {v} was updated to {convert_node_name_to_qconfig[k]}"
                    )
        node_name_to_qconfig = convert_node_name_to_qconfig

    custom_module_classes = get_custom_module_class_keys(
        convert_custom_config.observed_to_quantized_mapping
    )
    custom_module_class_mapping = convert_custom_config.observed_to_quantized_mapping

    if observed_graph_module_attrs.equalization_node_name_to_qconfig is not None:
        # If we want to do equalization then do the following:
        # Calculate the equalization scale, update the observers with the scaled
        # inputs, and scale the weight
        weight_eq_obs_dict = update_obs_for_equalization(model, modules)
        convert_eq_obs(model, modules, weight_eq_obs_dict)

    # always run weight observers in the top level forward method
    # for dynamic quant ops or weight only quant ops
    _run_weight_observers(model, backend_config)

    # additional state to override inputs to be quantized, if specified
    # by the user
    placeholder_node_seen_cnt = 0
    input_quantized_idxs: list[int] = prepare_custom_config.input_quantized_indexes
    output_quantized_idxs: list[int] = prepare_custom_config.output_quantized_indexes

    root_module_to_quantized_reference_module = (
        get_root_module_to_quantized_reference_module(backend_config)
    )
    # convert tuples so that it can work with isinstance(module, tuple_of_classes)
    root_module_classes = tuple(root_module_to_quantized_reference_module.keys())
    qat_module_classes = get_qat_module_classes(backend_config)
    fused_module_classes = get_fused_module_classes(backend_config)
    statically_quantized_custom_module_nodes: set[Node] = set()
    model_device = assert_and_get_unique_device(model)

    for node in list(model.graph.nodes):
        if node.op == "placeholder":
            cur_placeholder_node_idx = placeholder_node_seen_cnt
            placeholder_node_seen_cnt += 1
            if cur_placeholder_node_idx in input_quantized_idxs:
                # Inputs are assumed to be quantized if the user specified the
                # input_quantized_idxs override.
                # we need to dequantize the inputs since all operators took
                # floating point inputs in reference quantized models
                _insert_dequantize_node(node, model.graph)
        elif node.op == "output":
            # If the argument is empty we don't need to do anything
            if len(output_quantized_idxs) == 0:
                continue
            # Result are kept quantized if the user specified the
            # output_quantized_idxs override.
            # Remove the dequantize operator for the node in the end if any
            return_node = node
            output = node.args[0]
            # outputs can be Node, list, tuple, dict, other cases are not supported yet
            if isinstance(output, (list, tuple)):
                for idx in output_quantized_idxs:
                    _maybe_recursive_remove_dequantize(
                        output[idx], return_node, model.graph
                    )
            elif isinstance(output, (Node, dict)):
                # we treat dict as a single argument currently, but it can be extended
                # to support {"key": dtype} after we change output_quantized_idxs to
                # dict
                if 0 in output_quantized_idxs:
                    _maybe_recursive_remove_dequantize(output, return_node, model.graph)
            else:
                warnings.warn(
                    f"Unsupported node type for output_quantized_idxs: {type(output)}",
                    stacklevel=2,
                )
        elif node.op == "call_module":
            mod = _get_module(node, modules)
            if mod is None:
                raise AssertionError(
                    "Expected module for call_module node to be present in modules mapping"
                )
            if _is_activation_post_process(mod):
                observed_node = node.args[0]
                if observed_node in statically_quantized_custom_module_nodes:
                    _replace_observer_or_dequant_stub_with_dequantize_node(
                        node, model.graph
                    )
                else:
                    if is_decomposed:
                        _replace_observer_with_quantize_dequantize_node_decomposed(
                            model,
                            node,
                            modules,
                            node_name_to_scope,
                            node_name_to_qconfig,
                            model_device,
                        )
                    else:
                        _replace_observer_with_quantize_dequantize_node(
                            model,
                            node,
                            modules,
                            node_name_to_scope,
                            node_name_to_qconfig,
                            model_device,
                        )
            elif isinstance(mod, DeQuantStub):
                _replace_observer_or_dequant_stub_with_dequantize_node(
                    node, model.graph
                )
            elif _is_observed_standalone_module(mod):
                convert_standalone_module(
                    node, modules, model, is_reference, backend_config
                )
            # below this point `type_before_parametrizations` is used
            # instead of `type` to handle situations with fx quant + sparsity
            elif type_before_parametrizations(mod) in set(root_module_classes).union(
                qat_module_classes
            ).union(fused_module_classes):
                # extra check for fused module classes to make sure they are fused module classes
                # of target modules
                if (
                    type_before_parametrizations(mod) in fused_module_classes
                    and type_before_parametrizations(mod[0]) not in root_module_classes
                ):  # type: ignore[index]
                    continue
                convert_weighted_module(
                    node,
                    modules,
                    observed_node_names,
                    node_name_to_qconfig,
                    backend_config,
                    is_decomposed,
                    is_reference,
                    model_device,
                )
            elif type_before_parametrizations(mod) in custom_module_classes:
                convert_custom_module(
                    node,
                    model.graph,
                    modules,
                    custom_module_class_mapping,
                    statically_quantized_custom_module_nodes,
                )

    # remove deadcode after converting observers to quant/dequant ops
    model.graph.eliminate_dead_code()
    model = GraphModule(model, model.graph)

    # TODO: maybe move this to quantize_fx.py
    if not is_reference:
        model = lower_to_fbgemm(
            model, node_name_to_qconfig, node_name_to_scope, keep_original_weights
        )

    # TODO: this looks hacky, we want to check why we need this and see if we can
    # remove this
    # removes qconfig and activation_post_process modules
    if _remove_qconfig_flag:
        _remove_qconfig(model)
    model.delete_all_unused_submodules()
    model.meta.pop("_observed_graph_module_attrs", None)
    return model