def quantize_activation_bw(graph: torch.fx.Graph) -> None:
    bw_inputs = [node for node in graph.nodes if node.op == "placeholder"]
    activation_node = None
    for node in bw_inputs:
        if node.meta.get("saved_for_quantization", False):
            node.meta.pop("saved_for_quantization")
            dequant_type = node.meta.pop("dequant_type")
            # dequantize the node
            if torch._inductor.config.post_grad_fusion_options[
                "activation_quantization_aten_pass"
            ].get("use_scaling", False):
                # case: use scaling
                with graph.inserting_after(node):
                    # find corresponding scale node
                    scale_name = "fp8_scale_" + node.name.replace("fp8_quant_", "")
                    scale_node = next(
                        bwd_input
                        for bwd_input in bw_inputs
                        if bwd_input.name == scale_name
                    )
                with graph.inserting_after(scale_node):
                    activation_node = graph.call_function(
                        torch.ops.prims.convert_element_type.default,
                        args=(node, dequant_type),
                    )
                    activation_node.meta["val"] = (
                        torch.ops.prims.convert_element_type.default(
                            node.meta["val"], dequant_type
                        )
                    )
                    activation_node.meta["tensor_meta"] = extract_tensor_metadata(
                        activation_node.meta["val"]
                    )
                with graph.inserting_after(activation_node):
                    divided_target_node_32 = graph.call_function(
                        torch.ops.aten.div.Tensor,
                        args=(activation_node, scale_node),
                    )
                    divided_target_node_32.meta["val"] = torch.ops.aten.div.Tensor(
                        activation_node.meta["val"], scale_node.meta["val"]
                    )
                    divided_target_node_32.meta["tensor_meta"] = (
                        extract_tensor_metadata(divided_target_node_32.meta["val"])
                    )
                with graph.inserting_after(divided_target_node_32):
                    dequant_node = graph.call_function(
                        torch.ops.prims.convert_element_type.default,
                        args=(divided_target_node_32, dequant_type),
                    )
                    dequant_node.meta["val"] = (
                        torch.ops.prims.convert_element_type.default(
                            divided_target_node_32.meta["val"], dequant_type
                        )
                    )
                    dequant_node.meta["tensor_meta"] = extract_tensor_metadata(
                        dequant_node.meta["val"]
                    )
            else:
                with graph.inserting_after(node):
                    dequant_node = graph.call_function(
                        torch.ops.prims.convert_element_type.default,
                        args=(node, dequant_type),
                        name="dequant_" + str(node.name),
                    )
                    dequant_node.meta["val"] = (
                        torch.ops.prims.convert_element_type.default(
                            node.meta["val"], dequant_type
                        )
                    )
                    dequant_node.meta["tensor_meta"] = extract_tensor_metadata(
                        dequant_node.meta["val"]
                    )
            # find the users of the node and replace them with the new node except the dequant_node
            for user in list(node.users.keys()):
                if user != dequant_node and user != activation_node:
                    user.replace_input_with(node, dequant_node)

    counters["inductor"]["activation_quantization_bwd_aten_pass"] += 1