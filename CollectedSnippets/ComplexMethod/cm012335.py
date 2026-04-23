def _int_mm_weight_prepack(match: Match, *args, **kwargs):
            bias = kwargs.get("bias")
            x = kwargs["a"]
            weight = kwargs["b"]
            dtype = kwargs["dtype"]
            x_scale = kwargs["x_scale"]
            w_scale = kwargs["w_scale"]
            x_shape = x.meta.get("tensor_meta").shape
            if has_free_symbols(x_shape):
                # For dynamic shape case, we can't get activation shape ahead of runtime.
                x_shape = None

            out_node = match.output_node()
            with match.graph.inserting_before(out_node):
                transpose_node = match.graph.call_function(
                    aten.permute.default, args=(weight, [1, 0])
                )
                contig_node = match.graph.call_function(
                    aten.contiguous.default, args=(transpose_node,)
                )
                packed_weight_inputs = (
                    contig_node,
                    x_shape,
                )
                packed_weight_op = torch.ops.onednn.qlinear_prepack
                prepack_weight_node = match.graph.call_function(
                    packed_weight_op, args=packed_weight_inputs
                )

                dummy_zp = None
                w_scale = match.graph.call_function(
                    prims.convert_element_type.default, args=(w_scale, torch.float32)
                )

                x_scale_shape = x_scale.meta.get("tensor_meta").shape
                x_scale_is_scalar = False
                if not has_free_symbols(x_scale_shape):
                    prod = 1
                    for d in x_scale_shape:
                        prod *= d
                    x_scale_is_scalar = prod == 1

                new_args: tuple[Any, ...]
                if x_scale_is_scalar:
                    # in this case, we can call onednn.qlinear directly
                    new_args = (
                        x,
                        x_scale,
                        dummy_zp,  # x_zp
                        prepack_weight_node,
                        w_scale,
                        dummy_zp,  # w_zp
                        bias,
                        1.0,  # output_scale
                        0,  # output_zero_point
                        dtype,  # output_dtype
                        "none",  # post op name
                        [],  # post op args
                        "",  # post op algorithm
                    )
                    new_linear_node = match.graph.call_function(
                        torch.ops.onednn.qlinear_pointwise.tensor, args=new_args
                    )
                    out_node.replace_all_uses_with(new_linear_node)
                    new_linear_node.meta.update(out_node.meta)
                else:
                    # onednn.qlinear does not support per-channel quantization of x
                    # so in this case, we have to apply x scale and add bias ourselves after qlinear
                    in_shape = kwargs.get("in_shape")
                    if in_shape is None:
                        x_reshaped = x
                    else:
                        x_reshaped = match.graph.call_function(
                            aten.reshape.default, args=(x, in_shape)
                        )
                    new_args = (
                        x_reshaped,
                        1.0,  # x_scale
                        0,  # x_zp
                        prepack_weight_node,
                        w_scale,
                        dummy_zp,  # w_zp
                        None,  # bias
                        1.0,  # output_scale
                        0,  # output_zero_point
                        dtype,  # output_dtype
                        "none",  # post op name
                        [],  # post op args
                        "",  # post op algorithm
                    )
                    new_linear_node = match.graph.call_function(
                        torch.ops.onednn.qlinear_pointwise, args=new_args
                    )
                    # apply x scale
                    new_out_node = match.graph.call_function(
                        aten.mul.Tensor, args=(new_linear_node, x_scale)
                    )

                    # Add bias and reshape
                    has_outer_reshape = (
                        kwargs.get("out_shape_with_bias") is not None
                        or kwargs.get("out_shape_no_bias") is not None
                    )

                    if has_outer_reshape:
                        out_shape = kwargs.get(
                            "out_shape_with_bias", kwargs["out_shape_no_bias"]
                        )
                    if bias is not None:
                        new_out_node = match.graph.call_function(
                            aten.add.Tensor, args=(new_out_node, bias)
                        )
                        if has_outer_reshape:
                            new_out_node = match.graph.call_function(
                                aten.reshape.default,
                                args=(new_out_node, out_shape),  # type: ignore[possibly-undefined]
                            )
                    else:
                        if has_outer_reshape:
                            new_out_node = match.graph.call_function(
                                aten.reshape.default,
                                args=(new_out_node, out_shape),  # type: ignore[possibly-undefined]
                            )
                    out_node.replace_all_uses_with(new_out_node)
                    new_out_node.meta.update(out_node.meta)
                for node in reversed(match.nodes):
                    match.graph.erase_node(node)
                counters["inductor"]["qlinear_weight_prepack_matcher_count"] += 1
                counters["inductor"]["qlinear_weight_prepack_matcher_nodes"] += len(
                    match.nodes
                )