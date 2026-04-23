def _convert(
    module,
    mapping=None,
    inplace=False,
    is_reference=False,
    convert_custom_config_dict=None,
    use_precomputed_fake_quant=False,
):
    r"""Converts submodules in input module to a different module according to `mapping`
    by calling `from_float` method on the target module class

    Args:
        module: input module
        mapping: a dictionary that maps from source module type to target
                 module type, can be overwritten to allow swapping user defined
                 Modules
        inplace: carry out model transformations in-place, the original module
                 is mutated
        is_reference: a flag to enable quantized reference module
        use_precomputed_fake_quant: a flag to enable use of precomputed fake quant

    """
    if mapping is None:
        mapping = (
            get_default_static_quant_reference_module_mappings()
            if is_reference
            else get_default_static_quant_module_mappings()
        )
    if convert_custom_config_dict is None:
        convert_custom_config_dict = get_default_custom_config_dict()
    custom_module_class_mapping = convert_custom_config_dict.get(
        "observed_to_quantized_custom_module_class", {}
    )

    if not inplace:
        module = copy.deepcopy(module)
    reassign = {}
    for name, mod in module.named_children():
        # both fused modules and observed custom modules are
        # swapped as one unit
        if (
            not isinstance(mod, _FusedModule)
            and type_before_parametrizations(mod) not in custom_module_class_mapping
        ):
            _convert(
                mod,
                mapping,
                True,  # inplace
                is_reference,
                convert_custom_config_dict,
                use_precomputed_fake_quant=use_precomputed_fake_quant,
            )
        reassign[name] = swap_module(
            mod, mapping, custom_module_class_mapping, use_precomputed_fake_quant
        )

    for key, value in reassign.items():
        module._modules[key] = value

    return module