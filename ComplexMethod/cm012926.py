def get_node_first_input_and_output_type(
    node: Node,
    gm: GraphModule,
    logger_cls: Callable,
    node_type_to_io_type_map: dict[str, set[NSNodeTargetType]],
) -> tuple[NodeInputOrOutputType, NodeInputOrOutputType]:
    # TODO(future PR): clean this up
    FUNS_IO_TYPE_FP32 = node_type_to_io_type_map["funs_io_type_fp32"]
    FUNS_IO_TYPE_FP16 = node_type_to_io_type_map["funs_io_type_fp16"]
    FUNS_IO_TYPE_INT8 = node_type_to_io_type_map["funs_io_type_int8"]
    FUNS_IO_TYPE_FP32_OR_INT8 = node_type_to_io_type_map["funs_io_type_fp32_or_int8"]
    MODS_IO_TYPE_FP32 = node_type_to_io_type_map["mods_io_type_fp32"]
    MODS_IO_TYPE_INT8 = node_type_to_io_type_map["mods_io_type_int8"]
    MODS_IO_TYPE_FP32_OR_INT8 = node_type_to_io_type_map["mods_io_type_fp32_or_int8"]
    METHS_IO_TYPE_FP32_OR_INT8 = node_type_to_io_type_map["meths_io_type_fp32_or_int8"]

    if node.op == "call_function":
        if node.target in FUNS_IO_TYPE_FP32:
            return (NodeInputOrOutputType.FP32, NodeInputOrOutputType.FP32)
        if node.target in FUNS_IO_TYPE_FP16:
            return (NodeInputOrOutputType.FP16, NodeInputOrOutputType.FP16)
        elif node.target in FUNS_IO_TYPE_INT8:
            return (NodeInputOrOutputType.INT8, NodeInputOrOutputType.INT8)
        elif node.target in FUNS_IO_TYPE_FP32_OR_INT8:
            first_arg = get_normalized_nth_input(node, gm, 0)
            if not isinstance(first_arg, Node):
                raise AssertionError(f"Expected Node, got {type(first_arg)}")
            (
                _prev_node_input_type,
                prev_node_output_type,
            ) = get_node_first_input_and_output_type(
                first_arg, gm, logger_cls, node_type_to_io_type_map
            )
            return (prev_node_output_type, prev_node_output_type)
        else:
            return (NodeInputOrOutputType.UNKNOWN, NodeInputOrOutputType.UNKNOWN)

    elif node.op == "call_module":
        if node.op != "call_module":
            raise AssertionError(f"Expected call_module, got '{node.op}'")
        if not isinstance(node.target, str):
            raise AssertionError(f"Expected str, but got {type(node.target)}")

        mod = getattr_from_fqn(gm, node.target)
        is_known_fp32_or_int8_input_module = any(
            isinstance(mod, target_type)  # type: ignore[arg-type]
            for target_type in MODS_IO_TYPE_FP32_OR_INT8
        )
        if (
            isinstance(mod, (logger_cls, ObserverBase, FakeQuantizeBase))  # type: ignore[arg-type]
            or is_known_fp32_or_int8_input_module
        ):
            # A logger or observer's input and output type is the output
            # type of the preceding node.
            first_arg = get_normalized_nth_input(node, gm, 0)
            if not isinstance(first_arg, Node):
                raise AssertionError(f"Expected Node, got {type(first_arg)}")
            (
                _prev_node_input_type,
                prev_node_output_type,
            ) = get_node_first_input_and_output_type(
                first_arg, gm, logger_cls, node_type_to_io_type_map
            )
            return (prev_node_output_type, prev_node_output_type)
        is_known_fp32_input_module = any(
            isinstance(mod, target_type)  # type: ignore[arg-type]
            for target_type in MODS_IO_TYPE_FP32
        )
        is_known_int8_input_module = any(
            isinstance(mod, target_type)  # type: ignore[arg-type]
            for target_type in MODS_IO_TYPE_INT8
        )
        if is_known_fp32_input_module:
            return (NodeInputOrOutputType.FP32, NodeInputOrOutputType.FP32)
        elif is_known_int8_input_module:
            return (NodeInputOrOutputType.INT8, NodeInputOrOutputType.INT8)
        else:
            return (NodeInputOrOutputType.UNKNOWN, NodeInputOrOutputType.UNKNOWN)

    elif node.op == "call_method":
        if node.target == "dequantize":
            # Dequantize is a special node because it allows multiple input types.
            # So, we look up the output type of the previous node and return that
            # as the input type of this node instance.
            prev_node = get_normalized_nth_input(node, gm, 0)
            if not isinstance(prev_node, Node):
                raise AssertionError(f"Expected Node, got {type(prev_node)}")
            (
                _prev_node_input_type,
                prev_node_output_type,
            ) = get_node_first_input_and_output_type(
                prev_node, gm, logger_cls, node_type_to_io_type_map
            )
            return (prev_node_output_type, NodeInputOrOutputType.FP32)

        elif node.target == "to":
            # to is a special node because it allows multiple input types.
            # So, we look up the output type of the previous node and return that
            # as the input type of this node instance. We also look up the target
            # of to and return the correct output type.
            prev_node = get_normalized_nth_input(node, gm, 0)
            if not isinstance(prev_node, Node):
                raise AssertionError(f"Expected Node, got {type(prev_node)}")
            (
                _prev_node_input_type,
                prev_node_output_type,
            ) = get_node_first_input_and_output_type(
                prev_node, gm, logger_cls, node_type_to_io_type_map
            )

            cur_node_dtype_target = get_normalized_nth_input(node, gm, 1)
            if cur_node_dtype_target is not torch.float16:
                raise AssertionError(
                    f"{cur_node_dtype_target} handling needs to be added"
                )

            return (prev_node_output_type, NodeInputOrOutputType.FP16)

        elif node.target in METHS_IO_TYPE_FP32_OR_INT8:
            first_arg = get_normalized_nth_input(node, gm, 0)
            if not isinstance(first_arg, Node):
                raise AssertionError(f"Expected Node, got {type(first_arg)}")
            (
                _prev_node_input_type,
                prev_node_output_type,
            ) = get_node_first_input_and_output_type(
                first_arg, gm, logger_cls, node_type_to_io_type_map
            )
            return (prev_node_output_type, prev_node_output_type)

        return (NodeInputOrOutputType.UNKNOWN, NodeInputOrOutputType.UNKNOWN)
    else:
        return (NodeInputOrOutputType.UNKNOWN, NodeInputOrOutputType.UNKNOWN)