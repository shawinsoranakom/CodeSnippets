def convert_weighted_module(
    node: Node,
    modules: dict[str, torch.nn.Module],
    observed_node_names: set[str],
    node_name_to_qconfig: dict[str, QConfigAny],
    backend_config: BackendConfig,
    is_decomposed: bool = False,
    is_reference: bool = False,
    model_device: torch.device | None = None,
) -> None:
    """Convert a weighted module to reference quantized module in the model
    If the QConfig of a QAT module is not set, the module will still be converted to
    a float module.

    Args:
      - node: The call_module node of the observed standalone module
      - modules: named_module of original model
      - observed_node_names: names for the set of observed fx node, we can skip
        this conversion if the node is not observed
    """
    original_module = modules[str(node.target)]
    qconfig: QConfigAny = original_module.qconfig  # type: ignore[assignment]
    weight_post_process = None
    qat_module_classes = get_qat_module_classes(backend_config)

    if isinstance(original_module, qat_module_classes):
        # Converting qat module to a float module, we need to attach
        # weight fake_quant to the module, weight fake_quant is assumed to be run during
        # QAT so we don't need to run it again here
        weight_post_process = original_module.weight_fake_quant
        original_module = original_module.to_float()  # type: ignore[operator]
        # change qat module to float module
        parent_name, name = _parent_name(node.target)
        setattr(modules[parent_name], name, original_module)

    is_observed = node.name in observed_node_names
    # If a qconfig is not defined for this node, then skip converting to a reference module
    if (
        qconfig is None
        or _has_none_qconfig(node, node_name_to_qconfig)
        or not is_observed
    ):
        return

    # skip converting to reference quantized module if the qconfig is not supported
    pattern_to_dtype_configs = get_pattern_to_dtype_configs(backend_config)
    dtype_configs = pattern_to_dtype_configs.get(type(original_module), [])
    if not _is_qconfig_supported_by_dtype_configs(qconfig, dtype_configs):
        return

    # TODO: rename weight_is_statically_quantized to weight_is_int8_quantized
    is_weight_quantized = weight_is_quantized(qconfig)

    # the condition for swapping the module to reference quantized module is:
    # weights need to be quantized
    if not is_weight_quantized:
        return

    fused_module = None
    float_module = original_module
    # extract the individual float_module and fused module
    if isinstance(original_module, torch.ao.nn.intrinsic._FusedModule):
        fused_module = float_module
        float_module = fused_module[0]  # type: ignore[index]

    # TODO: move this to the reference quantized module
    # weight_qparams or weight_qparams dict
    wq_or_wq_dict = {"is_decomposed": is_decomposed}
    if isinstance(float_module, torch.nn.RNNCellBase):
        weight_post_process_ih = qconfig.weight()  # type: ignore[union-attr, operator]
        weight_post_process_hh = qconfig.weight()  # type: ignore[union-attr, operator]
        weight_post_process_ih(float_module.weight_ih)
        weight_post_process_hh(float_module.weight_hh)
        weight_qparams_ih = get_qparam_dict(weight_post_process_ih)
        weight_qparams_hh = get_qparam_dict(weight_post_process_hh)
        wq_or_wq_dict.update(
            {
                "weight_ih": weight_qparams_ih,
                "weight_hh": weight_qparams_hh,
            }
        )
    elif isinstance(float_module, (torch.nn.LSTM, torch.nn.GRU)):
        # format for wq_or_wq_dict (flattened attributes):
        # {"weight_ih_l0_scale": ..., "weight_ih_l0_qscheme": ..., ...}
        for wn in float_module._flat_weights_names:
            if hasattr(float_module, wn) and wn.startswith("weight"):
                weight = getattr(float_module, wn)
                weight_post_process = qconfig.weight()  # type: ignore[union-attr, operator]
                if weight_post_process.dtype == torch.qint8:  # type: ignore[union-attr]
                    weight_post_process(weight)  # type: ignore[operator, misc]
                wq_or_wq_dict[wn] = get_qparam_dict(weight_post_process)
    else:
        # weight_post_process is None means the original module is not a QAT module
        # we need to get weight_post_process from qconfig in this case
        is_ptq = weight_post_process is None
        if is_ptq:
            weight_post_process = qconfig.weight()  # type: ignore[union-attr, operator]
            if model_device is not None:
                device = model_device
            else:
                device = assert_and_get_unique_device(float_module)
            if device:
                weight_post_process.to(device)

        # Call weight observer/fake_quant at least once to ensure the scales and zero points
        # have the right shapes. Note: there are two cases where we don't have to do this:
        #
        # (1) QAT: The model's forward method already calls the weight observer/fake_quant,
        #     and this typically happens during training, so we don't need to do it here.
        #
        # (2) Non-reference (lowered) case: The quantized module's from_float method already
        #     calls the weight observer/fake_quant, so we don't have to do it here.
        #
        # Currently we ignore both cases and call the weight observer/fake_quant here
        # regardless, which is technically incorrect. For (1), this is mainly to preserve BC
        # in test code, which may not always train before convert. In the future, we should
        # break BC for these two cases. See https://github.com/pytorch/pytorch/issues/73941.
        #
        # For PT2, however, we don't need to preserve BC here, so we can skip this hack
        # for QAT. We identify this case as (is_decomposed + is_reference + is_qat).
        # Note that we still need it for PTQ in the PT2 flow since the model's forward
        # method doesn't call the weight observer.
        is_qat = not is_ptq
        if not (is_decomposed and is_reference and is_qat):
            weight_post_process(float_module.weight)  # type: ignore[operator]

        wq_or_wq_dict.update(get_qparam_dict(weight_post_process))

    # We use the same reference module for all modes of quantization: static, dynamic, weight_only
    # root_module_to_quantized_reference_module: module mapping from root (floating point) module class
    # to quantized reference module class, e.g. nn.Conv2d to nn.quantized._reference.Conv2d
    root_module_to_quantized_reference_module = (
        get_root_module_to_quantized_reference_module(backend_config)
    )
    ref_qmodule_cls = root_module_to_quantized_reference_module.get(
        type_before_parametrizations(float_module), None
    )
    if ref_qmodule_cls is None:
        raise AssertionError(
            f"No reference quantized module class configured for {type_before_parametrizations(float_module)}"
        )
    ref_qmodule = ref_qmodule_cls.from_float(float_module, wq_or_wq_dict)  # type: ignore[attr-defined]
    if fused_module is not None:
        fused_module[0] = ref_qmodule  # type: ignore[operator]
    else:
        parent_name, name = _parent_name(node.target)
        setattr(modules[parent_name], name, ref_qmodule)