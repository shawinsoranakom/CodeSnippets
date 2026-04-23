def get_node_input_qparams(
    node: Node,
    gm: GraphModule,
    node_type_to_io_type_map: dict[str, set[NSNodeTargetType]],
) -> tuple[torch.Tensor | float, torch.Tensor | int] | None:
    """
    Returns the qparams (scale, zero_point) of the first input to `node`,
    if they can be inferred from the graph.
    """
    prev_node = get_normalized_nth_input(node, gm, 0)

    if not isinstance(prev_node, Node):
        return None

    MODS_IO_TYPE_FP32_OR_INT8 = node_type_to_io_type_map["mods_io_type_fp32_or_int8"]

    def _get_scale_zp_from_function_args(node, gm, scale_arg_idx, zp_arg_idx):
        scale_node = get_normalized_nth_input(node, gm, scale_arg_idx)
        zp_node = get_normalized_nth_input(node, gm, zp_arg_idx)
        if not isinstance(scale_node, Node):
            raise AssertionError(f"Expected Node, got {type(scale_node)}")
        if not isinstance(scale_node.target, str):
            raise AssertionError(f"Expected str, got {type(scale_node.target)}")
        if not isinstance(zp_node, Node):
            raise AssertionError(f"Expected Node, got {type(zp_node)}")
        if not isinstance(zp_node.target, str):
            raise AssertionError(f"Expected str, got {type(zp_node.target)}")
        scale_obj = getattr_from_fqn(gm, scale_node.target)
        zp_obj = getattr_from_fqn(gm, zp_node.target)
        return (scale_obj, zp_obj)

    if prev_node.op == "call_function":
        # quantize - read the args directly
        if prev_node.target is torch.quantize_per_tensor:
            return _get_scale_zp_from_function_args(prev_node, gm, 1, 2)
        elif prev_node.target in (toq.add, toq.add_relu, toq.mul, toq.mul_relu):
            return _get_scale_zp_from_function_args(prev_node, gm, 2, 3)

        return None
        # TODO(future PR): handle more functionals
        # TODO(future PR): handle functional ops which inherit qparams from input

    elif prev_node.op == "call_module":
        # get type of the module
        if not isinstance(prev_node.target, str):
            raise AssertionError(f"Expected str, got {type(prev_node.target)}")
        module_obj = getattr_from_fqn(gm, prev_node.target)
        if isinstance(
            module_obj,
            (
                nnq.Linear,
                nnq.Conv1d,
                nnq.Conv2d,
                nniq.ConvReLU2d,
                nnq.Conv3d,
                nnq.BatchNorm2d,
                nnq.BatchNorm3d,
                nnq.ConvTranspose1d,
                nnq.ConvTranspose2d,
                nnq.ELU,
                nnq.GroupNorm,
                nnq.InstanceNorm1d,
                nnq.InstanceNorm2d,
                nnq.InstanceNorm3d,
                nnq.LayerNorm,
                nnq.Hardswish,
                nnq.LeakyReLU,
                nnq.ReLU6,
                nniq.BNReLU2d,
                nniq.BNReLU3d,
                nniq.ConvReLU1d,
                nniq.ConvReLU2d,
                nniq.ConvReLU3d,
                nniq.LinearReLU,
            ),
        ):
            return (module_obj.scale, module_obj.zero_point)  # type: ignore[return-value]

        is_known_fp32_or_int8_input_module = any(
            isinstance(module_obj, target_type)  # type: ignore[arg-type]
            for target_type in MODS_IO_TYPE_FP32_OR_INT8
        )
        if is_known_fp32_or_int8_input_module:
            return get_node_input_qparams(prev_node, gm, node_type_to_io_type_map)

    return None