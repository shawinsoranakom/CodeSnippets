def enable_activation_quantization(
    saved_values: list[fx.Node],
    fwd_module: fx.GraphModule,
    bwd_module: fx.GraphModule,
    static_lifetime_input_nodes: OrderedSet[fx.Node] | None = None,
    num_fwd_outputs: int = 0,
) -> None:
    static_input_names: list[str] = (
        [node.name for node in static_lifetime_input_nodes]
        if static_lifetime_input_nodes
        else []
    )
    saved_values_names = {node.name: node for node in saved_values}
    if torch._inductor.config.post_grad_fusion_options[
        "activation_quantization_aten_pass"
    ].get("exclude_primals", False):
        saved_values_names = {
            node.name: node for node in saved_values if "primals" not in node.name
        }
    fwd_module_outputs = fwd_module.graph.find_nodes(op="output")[0].args[0]
    bwd_module_inputs = {
        node.name: node for node in bwd_module.graph.find_nodes(op="placeholder")
    }
    should_perform_fp8_quant = False
    for node in fwd_module_outputs:
        if node.name in saved_values_names and should_quantize(node):
            if node.name in static_input_names:
                log.debug("Skipping quantization of static input %s: ", node.name)
                continue
            node.meta["saved_for_quantization"] = True
            node.meta["dequant_type"] = node.meta["val"].dtype
            # some of the fwd outputs and bwd inputs are not share the same object
            bwd_module_inputs[node.name].meta["saved_for_quantization"] = True
            bwd_module_inputs[node.name].meta["dequant_type"] = node.meta["val"].dtype
            should_perform_fp8_quant = True

    if should_perform_fp8_quant:
        perform_fp8_activation_quantization(
            fwd_module, bwd_module, bwd_module_inputs, num_fwd_outputs
        )