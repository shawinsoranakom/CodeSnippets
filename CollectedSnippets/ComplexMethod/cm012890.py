def _replace_observer_with_quantize_dequantize_node_decomposed(
    model: torch.fx.GraphModule,
    node: Node,
    modules: dict[str, torch.nn.Module],
    node_name_to_scope: dict[str, tuple[str, type]],
    node_name_to_qconfig: dict[str, QConfigAny],
    model_device: torch.device | None = None,
) -> None:
    """Replace activation_post_process module call node with quantize and
    dequantize node working with decomposed Tensor

    Before:
    ... -> observer_0(x) -> ...
    After:
    ... -> torch.ops.quantized_decomposed.quantize_per_tensor(x, ...) ->
    torch.ops.quantized_decomposed.dequantize_per_tensor() -> ...

    or quantize_per_channel and dequantize_per_channel
    """
    graph = model.graph
    if modules is None:
        raise AssertionError("modules must not be None")
    if not isinstance(node.target, str):
        raise AssertionError(
            f"Expected node.target to be a str, but got {type(node.target)}"
        )
    module_path, prefix = _get_module_path_and_prefix(
        node, node_name_to_scope, node_name_to_qconfig
    )
    activation_post_process = modules[node.target]
    if hasattr(activation_post_process, "convert"):
        activation_post_process.convert(model, node)
        return
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

    # 1. extract the information from activation_post_process module for generating
    # the quantize and dequantize operator
    dtype = activation_post_process.dtype  # type: ignore[attr-defined]

    is_dynamic = False
    if hasattr(activation_post_process, "is_dynamic"):
        is_dynamic = activation_post_process.is_dynamic  # type: ignore[assignment]

    def add_dequantize_op_kwargs(dequantize_op, input_node):
        dequantize_op_kwargs = {}
        if "val" in input_node.meta:
            dq_out_dtype = input_node.meta["val"].dtype
            if dq_out_dtype != torch.float32:
                dequantize_op_kwargs = {"out_dtype": dq_out_dtype}
        return dequantize_op_kwargs

    if dtype in SUPPORTED_QDTYPES and (not is_dynamic):
        # TODO: probably should cleanup this condition check, it's hard
        # to reason about this if and the following elif

        # uint8/int8/int32 static quantization branch

        # 1. extract information for inserting q/dq node from activation_post_process
        node_type = "call_function"
        quantize_op: Callable | None = None
        scale, zero_point = activation_post_process.calculate_qparams()  # type: ignore[attr-defined, operator]
        if is_per_channel(activation_post_process.qscheme):  # type: ignore[attr-defined]
            ch_axis = int(activation_post_process.ch_axis)  # type: ignore[attr-defined, arg-type]
            quantize_op = torch.ops.quantized_decomposed.quantize_per_channel.default
            dequantize_op = (
                torch.ops.quantized_decomposed.dequantize_per_channel.default
            )
            quant_min = activation_post_process.quant_min
            quant_max = activation_post_process.quant_max
            dtype_ = to_underlying_dtype(dtype)
            qparams = {
                "_scale_": scale,
                "_zero_point_": zero_point,
                "_axis_": ch_axis,
                "_quant_min_": quant_min,
                "_quant_max_": quant_max,
                "_dtype_": dtype_,
            }
        else:
            quantize_op = torch.ops.quantized_decomposed.quantize_per_tensor.default
            dequantize_op = torch.ops.quantized_decomposed.dequantize_per_tensor.default
            scale = float(scale)
            zero_point = int(zero_point)
            quant_min = activation_post_process.quant_min  # type: ignore[attr-defined]
            quant_max = activation_post_process.quant_max  # type: ignore[attr-defined]
            dtype_ = to_underlying_dtype(dtype)
            qparams = {
                "_scale_": scale,
                "_zero_point_": zero_point,
                "_quant_min_": quant_min,
                "_quant_max_": quant_max,
                "_dtype_": dtype_,
            }

        # 2. replace activation_post_process node with quantize and dequantize
        with graph.inserting_before(node):
            input_node = node.args[0]
            quantize_op_inputs = [input_node]
            for key, value_or_node in qparams.items():
                # TODO: we can add the information of whether a value needs to
                # be registered as an attribute in qparams dict itself
                if key in ["_scale_", "_zero_point_"] and (
                    not isinstance(value_or_node, (float, int))
                ):
                    # For scale and zero_point values we register them as buffers in the root module.
                    # However, note that when the values are not tensors, as in the case of
                    # per_tensor quantization, they will be treated as literals.
                    # However, registering them as a node seems to cause issue with dynamo
                    # tracing where it may consider tensor overload as opposed to default.
                    # With extra check of scale and zero_point being scalar, it makes
                    # sure that the default overload can be used.
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
            # use the same qparams from quantize op
            dq_inputs = [quantized_node] + quantize_op_inputs[1:]
            dequantized_node = graph.call_function(
                dequantize_op,
                tuple(dq_inputs),
                add_dequantize_op_kwargs(dequantize_op, input_node),
            )

            node.replace_all_uses_with(dequantized_node)
            # propagate numeric debug handle from observer/fake_quant node to dequantize node
            if (
                CUSTOM_KEY in node.meta
                and NUMERIC_DEBUG_HANDLE_KEY in node.meta[CUSTOM_KEY]
            ):
                raise NotImplementedError(
                    "pt2e numeric suite has been migrated to torchao (https://github.com/pytorch/ao)"
                )
            graph.erase_node(node)
    elif is_dynamic:
        # uint8/int8/fp16 dynamic quantization

        # 1. extract information for inserting q/dq node from activation_post_process
        node_type = "call_function"
        quantize_op = torch.ops.quantized_decomposed.quantize_per_tensor.tensor
        # we only use choose_qparams for is_decomposed now,
        # but we should probably align the non-decomposed path with this as well,
        # and that can be done after we remove reduce_range flag
        # 1. extract qparams from activation_post_process module
        dtype_ = to_underlying_dtype(dtype)
        if dtype_ not in [torch.uint8, torch.int8]:
            raise AssertionError(
                "only uint8 and int8 are supported in reference flow for dynamic quantization right now"
            )
        quant_min = activation_post_process.quant_min  # type: ignore[attr-defined]
        quant_max = activation_post_process.quant_max  # type: ignore[attr-defined]
        qscheme = getattr(activation_post_process, "qscheme", torch.per_tensor_affine)  # type: ignore[attr-defined]
        eps = getattr(activation_post_process, "eps", torch.finfo(torch.float32).eps)  # type: ignore[attr-defined]
        # note: scale and zero_point are missing for quantize_per_tensor op
        # we'll need to get this from choose_qparams op, which we'll add after
        # this step
        qparams = {
            "_quant_min_": quant_min,
            "_quant_max_": quant_max,
            "_eps_": eps,
            "_dtype_": dtype_,
        }

        choose_qparams_op = _QSCHEME_TO_CHOOSE_QPARAMS_OP[qscheme]
        # 2. insert choose_qparams op and update the qparams list
        with graph.inserting_before(node):
            input_node = node.args[0]
            choose_qparams_op_inputs = [node.args[0]] + list(qparams.values())
            choose_qparams_node = graph.create_node(
                "call_function", choose_qparams_op, tuple(choose_qparams_op_inputs), {}
            )
            # choose_qparms returns (scale, zero_point)
            scale_node = graph.create_node(
                "call_function", operator.getitem, (choose_qparams_node, 0), {}
            )
            zero_point_node = graph.create_node(
                "call_function", operator.getitem, (choose_qparams_node, 1), {}
            )
            # we have quant_min, quant_max and dtype, all should be stored
            # as literals
            quant_min = qparams["_quant_min_"]
            quant_max = qparams["_quant_max_"]
            dtype = qparams["_dtype_"]
            qparams = {
                "_scale_": scale_node,
                "_zero_point_": zero_point_node,
                "_quant_min_": quant_min,
                "_quant_max_": quant_max,
                "_dtype_": dtype,
            }

        # 3. replace activation_post_process node to quantize and dequantize node
        with graph.inserting_before(node):
            input_node = node.args[0]
            quantize_op_inputs = [input_node]
            for key, value_or_node in qparams.items():
                # TODO: we can add the information of whether a value needs to
                # be registered as an attribute in qparams dict itself
                if key in ["_scale_", "_zero_point_"]:
                    # in this case we have a node in the graph since it's dynamically
                    # computed from the input, with choose_qparams op
                    qparam_node = value_or_node
                    quantize_op_inputs.append(qparam_node)
                else:
                    # for qparams that are not scale/zero_point (like axis, dtype) we
                    # store them as literals in the graph.
                    quantize_op_inputs.append(value_or_node)

            quantized_node = graph.create_node(
                node_type, quantize_op, tuple(quantize_op_inputs), {}
            )
            # use the same qparams from quantize op
            dq_inputs = [quantized_node] + quantize_op_inputs[1:]
            # need to use the tensor variant of this op, since scale and zero_point
            # from choose_qparam are Tensors, instead of float/int, this is to
            # prevent these nodes being traced away by downstream systems
            dequantize_op = torch.ops.quantized_decomposed.dequantize_per_tensor.tensor
            dequantized_node = graph.call_function(
                dequantize_op,
                tuple(dq_inputs),
                add_dequantize_op_kwargs(dequantize_op, input_node),
            )

            node.replace_all_uses_with(dequantized_node)
            # propagate numeric debug handle from observer/fake_quant node to dequantize node
            if NUMERIC_DEBUG_HANDLE_KEY in node.meta:
                raise NotImplementedError(
                    "pt2e numeric suite has been migrated to torchao (https://github.com/pytorch/ao)"
                )
            graph.erase_node(node)
    elif dtype == torch.float16:
        # Insert to_fp16 -> to_fp32 node
        dtype_convert_op = torch.ops.quantized_decomposed.convert_element_type.no_fuse
        with graph.inserting_before(node):
            input_node = node.args[0]
            convert_fp16_node = graph.create_node(
                "call_function", dtype_convert_op, (input_node, torch.float16), {}
            )
            convert_fp32_node = graph.create_node(
                "call_function", dtype_convert_op, (convert_fp16_node, torch.float), {}
            )
            node.replace_all_uses_with(convert_fp32_node)
            graph.erase_node(node)