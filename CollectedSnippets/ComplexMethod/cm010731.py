def quantize_activation_fw(graph: torch.fx.Graph, num_fwd_outputs: int = 0) -> None:
    output = graph.find_nodes(op="output")[0]
    fwd_outputs = output.args[0]
    quant_type = get_quant_type()
    clamp_min, clamp_max = calculate_range(quant_type)
    position_to_quant = dict()
    tensor_scale_nodes: list[fx.Node] = []
    sym_scale_nodes: list[fx.Node] = []
    for position, node in enumerate(fwd_outputs):
        # Don't quantize user-visible forward outputs. A tensor may appear as
        # both a user output and a saved-for-backward activation (same FX node
        # at two positions). Quantizing the user output position would:
        # 1. Return fp8 to the user instead of the original precision
        # 2. Create duplicate fp8_quant/fp8_scale backward placeholders that
        #    shift the stride mapping in _aot_stage2b_bw_compile (T264303372)
        if position < num_fwd_outputs:
            continue
        # check if the activation node is the node saved for quantization
        if node.meta.get("saved_for_quantization", False):
            # case: use scaling
            if torch._inductor.config.post_grad_fusion_options[
                "activation_quantization_aten_pass"
            ].get("use_scaling", True):
                # calculating the scale
                scale_node = calculate_quantization_scaling(
                    graph, node, clamp_max, 1e-12, position
                )

                # converting to fp8
                quant_node = perform_quantization(
                    graph, node, scale_node, quant_type, clamp_min, clamp_max, position
                )
                if not is_sym_node(scale_node):
                    tensor_scale_nodes.append(scale_node)
                else:
                    sym_scale_nodes.append(scale_node)
            else:
                # case: do not use scaling
                with graph.inserting_after(node):
                    quant_node = graph.call_function(
                        torch.ops.prims.convert_element_type.default,
                        args=(node, quant_type),
                        name=f"fp8_quant_pos_{position}_{node.name}",
                    )
                    quant_node.meta["val"] = (
                        torch.ops.prims.convert_element_type.default(
                            node.meta["val"], quant_type
                        )
                    )
                    quant_node.meta["tensor_meta"] = extract_tensor_metadata(
                        quant_node.meta["val"]
                    )

            position_to_quant[position] = quant_node

    # Use position-based lookup for building output
    # only update the return node args, and remain all other users unchanged
    output_updated_args = [
        position_to_quant.get(i, node) for i, node in enumerate(fwd_outputs)
    ]
    # add the scale nodes to the output find the first sym_node in the output
    # pyrefly: ignore [bad-argument-type]
    idx = find_first_sym_node(output_updated_args)
    scale_nodes = tensor_scale_nodes + sym_scale_nodes
    if scale_nodes:
        output_updated_args = (
            output_updated_args[:idx] + scale_nodes + output_updated_args[idx:]
        )

    output.update_arg(0, tuple(output_updated_args))
    counters["inductor"]["activation_quantization_fwd_aten_pass"] += 1