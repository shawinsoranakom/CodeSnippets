def _replace_observer_with_quantize_dequantize_node(
    model: torch.fx.GraphModule,
    node: Node,
    modules: dict[str, torch.nn.Module],
    node_name_to_scope: dict[str, tuple[str, type]],
    node_name_to_qconfig: dict[str, QConfigAny],
    model_device: torch.device | None = None,
) -> None:
    """Replace activation_post_process module call node with quantize and
    dequantize node

    Before:
    ... -> observer_0(x) -> ...
    After:
    ... -> torch.quantize_per_tensor(x, ...) -> x.dequantize() -> ...
    """
    if modules is None:
        raise AssertionError("modules must not be None")
    if not isinstance(node.target, str):
        raise AssertionError(
            f"Expected node.target to be a str, but got {type(node.target)}"
        )
    graph = model.graph
    module_path, prefix = _get_module_path_and_prefix(
        node, node_name_to_scope, node_name_to_qconfig
    )
    activation_post_process = modules[node.target]
    # skip replacing observers to quant/dequant nodes if the qconfigs of all
    # consumers and producers of this observer are None
    skip_replacement = all(
        _has_none_qconfig(n, node_name_to_qconfig)
        for n in list(node.args) + list(node.users.keys())
    )
    if skip_replacement or not _is_conversion_supported(activation_post_process):
        # didn't find corresponding quantize op and info for the activation_post_process
        # so we just remove the observer
        with graph.inserting_before(node):
            node.replace_all_uses_with(node.args[0])
            graph.erase_node(node)
        return

    # otherwise, we can convert the activation_post_process module call to quantize/dequantize node
    dtype = activation_post_process.dtype  # type: ignore[attr-defined]

    is_dynamic = False
    if hasattr(activation_post_process, "is_dynamic"):
        is_dynamic = activation_post_process.is_dynamic  # type: ignore[attr-defined, assignment]

    if dtype in [
        torch.quint8,
        torch.qint8,
        torch.qint32,
        torch.float8_e5m2,
        torch.float8_e4m3fn,
    ] and (not is_dynamic):
        # TODO: probably should cleanup this condition check, it's hard
        # to reason about this if and the following elif

        # uint8/int8/int32 static quantization branch

        # 1. extract the information from activation_post_process module for generating
        # the quantize and dequantize operator
        node_type = "call_function"
        quantize_op: Callable | None = None
        scale, zero_point = activation_post_process.calculate_qparams()  # type: ignore[attr-defined, operator]
        if is_per_channel(activation_post_process.qscheme):  # type: ignore[attr-defined]
            ch_axis = int(activation_post_process.ch_axis)  # type: ignore[attr-defined, arg-type]
            qparams = {
                "_scale_": scale,
                "_zero_point_": zero_point,
                "_axis_": ch_axis,
                "_dtype_": dtype,
            }
            quantize_op = torch.quantize_per_channel
        else:
            scale = float(scale)
            zero_point = int(zero_point)
            qparams = {"_scale_": scale, "_zero_point_": zero_point, "_dtype_": dtype}
            quantize_op = torch.quantize_per_tensor

        # 2. replace activation_post_process node with quantize and dequantize
        with graph.inserting_before(node):
            input_node = node.args[0]
            quantize_op_inputs = [input_node]
            for key, value_or_node in qparams.items():
                # TODO: we can add the information of whether a value needs to
                # be registered as an attribute in qparams dict itself
                if key in ["_scale_", "_zero_point_"]:
                    # For scale and zero_point values we register them as buffers in the root module.
                    # TODO: maybe need more complex attr name here
                    qparam_node = create_getattr_from_value(
                        model,
                        graph,
                        module_path + prefix + key,
                        value_or_node,
                        model_device,
                    )
                    quantize_op_inputs.append(qparam_node)
                else:
                    # for qparams that are not scale/zero_point (like axis, dtype) we store them as literals in the graph.
                    quantize_op_inputs.append(value_or_node)

            quantized_node = graph.create_node(
                node_type, quantize_op, tuple(quantize_op_inputs), {}
            )
            dequantized_node = graph.call_method("dequantize", args=(quantized_node,))
            node.replace_all_uses_with(dequantized_node)
            graph.erase_node(node)
    elif is_dynamic:
        # uint8/int8/fp16 dynamic quantization branch

        node_type = "call_function"
        quantize_op = torch.quantize_per_tensor_dynamic
        # TODO: get reduce range from observer
        # reduce_range = activation_post_process.reduce_range
        reduce_range = torch.backends.quantized.engine in ("fbgemm", "x86")
        qparams = {"_dtype_": dtype, "_reduce_range_": reduce_range}

        with graph.inserting_before(node):
            input_node = node.args[0]
            quantize_op_inputs = [input_node]
            for value in qparams.values():
                quantize_op_inputs.append(value)

            quantized_node = graph.create_node(
                node_type, quantize_op, tuple(quantize_op_inputs), {}
            )
            dequantized_node = graph.call_method("dequantize", args=(quantized_node,))
            node.replace_all_uses_with(dequantized_node)
            graph.erase_node(node)
    elif dtype == torch.float16:
        node_type = "call_method"
        quantize_op = "to"  # type: ignore[assignment]
        qparams = {"_dtype_": dtype}
        with graph.inserting_before(node):
            input_node = node.args[0]
            quantize_op_inputs = [input_node]
            for value in qparams.values():
                # TODO: we can add the information of whether a value needs to
                # be registered as an attribute in qparams dict itself
                quantize_op_inputs.append(value)

            quantized_node = graph.create_node(
                node_type, quantize_op, tuple(quantize_op_inputs), {}
            )
            dequantized_node = graph.call_method("dequantize", args=(quantized_node,))
            node.replace_all_uses_with(dequantized_node)
            graph.erase_node(node)