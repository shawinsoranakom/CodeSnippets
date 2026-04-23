def _lower_dynamic_weighted_ref_module(model: GraphModule):
    """
    Traverse the graph and find quantize_per_tensor_dynamic - dequantize - ref_module patterns
    and replace them with the dynamically quantized version of the ref module.
    """
    named_modules = dict(model.named_modules(remove_duplicate=False))
    for n in model.graph.nodes:
        if n.op != "call_module" or type(named_modules[str(n.target)]) not in set(
            DYNAMIC_LOWER_MODULE_MAP.keys()
        ).union(set(DYNAMIC_LOWER_FUSED_MODULE_MAP.keys())):
            continue
        ref_node = n
        dq_node = ref_node.args[0]
        if dq_node.op != "call_method" or dq_node.target != "dequantize":
            continue

        input_dynamic_q_node = dq_node.args[0]

        if (
            input_dynamic_q_node.op != "call_function"
            or input_dynamic_q_node.target != torch.quantize_per_tensor_dynamic
        ):
            continue

        activation_dtype = input_dynamic_q_node.args[1]
        is_fp16 = activation_dtype == torch.float16
        is_int8 = activation_dtype in [torch.quint8, torch.qint8]
        if not is_int8 and not is_fp16:
            continue

        ref_module = named_modules[str(ref_node.target)]
        ref_class = type(ref_module)
        if ref_class in DYNAMIC_LOWER_FUSED_MODULE_MAP:
            inner_ref_class, q_class = DYNAMIC_LOWER_FUSED_MODULE_MAP[ref_class]
            if type(ref_module[0]) is not inner_ref_class:
                continue
        else:
            q_class = DYNAMIC_LOWER_MODULE_MAP.get(ref_class)  # type: ignore[assignment]
        # TODO: maybe define a WeightedDynamicallyQuantizedModule
        q_module = q_class.from_reference(ref_module)  # type: ignore[attr-defined]

        # replace reference module with dynamically quantized module
        parent_name, module_name = _parent_name(ref_node.target)
        setattr(named_modules[parent_name], module_name, q_module)
        ref_node.replace_input_with(dq_node, input_dynamic_q_node.args[0])