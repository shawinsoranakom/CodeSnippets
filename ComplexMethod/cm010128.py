def _populate_param_buffer_metadata_to_new_gm(
    params_buffers_to_node_meta: dict[str, Any],
    gm: torch.fx.GraphModule,
    new_sig: "ExportGraphSignature",
) -> None:
    """
    Given that we collected param'buffer metadata before, we put them back in
    newly traced graph module
    """
    # Don't copy over nn_module_stack, stack_trace metadata for params/buffers nodes
    for metadata in params_buffers_to_node_meta.values():
        metadata.pop("nn_module_stack", None)
        metadata.pop("stack_trace", None)

    for node in gm.graph.nodes:
        if node.op == "placeholder":
            if node.target in new_sig.inputs_to_parameters:
                param_name = new_sig.inputs_to_parameters[node.target]
                if param_name in params_buffers_to_node_meta:
                    for k, v in params_buffers_to_node_meta[param_name].items():
                        node.meta[k] = v
            if node.target in new_sig.inputs_to_buffers:
                buffer_name = new_sig.inputs_to_buffers[node.target]
                if buffer_name in params_buffers_to_node_meta:
                    for k, v in params_buffers_to_node_meta[buffer_name].items():
                        node.meta[k] = v