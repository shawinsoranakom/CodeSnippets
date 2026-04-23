def convert_standalone_module(
    node: Node,
    modules: dict[str, torch.nn.Module],
    model: torch.fx.GraphModule,
    is_reference: bool,
    backend_config: BackendConfig | None,
) -> None:
    """Converts a observed standalone module to a quantized standalone module by calling
    the fx convert api, currently using the same `is_reference` flag as parent, but we may
    changing this behavior in the future (e.g. separating quantization and lowering for
    standalone module as well)

    Args:
      - node: The call_module node of the observed standalone module
      - modules: named_module of original model
      - model: original model
      - is_reference: a flag from parent provided by user to decide if we want to
        produce a reference model or a fbgemm/qnnpack model
      - backend_config: backend configuration of the target backend of quantization
    """
    # TODO: remove is_reference flag
    if is_reference:
        convert_fn = torch.ao.quantization.quantize_fx.convert_to_reference_fx
    else:
        convert_fn = torch.ao.quantization.quantize_fx.convert_fx  # type: ignore[attr-defined]
    # We know that observed standalone module is a GraphModule since
    # it's produced by us
    observed_standalone_module: GraphModule = modules[str(node.target)]  # type: ignore[assignment]
    sm_input_quantized_idxs = observed_standalone_module.meta[
        "_observed_graph_module_attrs"
    ].standalone_module_input_quantized_idxs
    # remove the dequantize nodes for inputs
    args = list(node.args)
    for idx in range(len(args)):
        if idx in sm_input_quantized_idxs:
            arg = args[idx]
            if arg.op == "call_method" and arg.target == "dequantize":  # type: ignore[union-attr]
                quantize_node = arg.args[0]  # type: ignore[union-attr]
                node.replace_input_with(arg, quantize_node)
                if len(arg.users) == 0:  # type: ignore[union-attr]
                    model.graph.erase_node(arg)
    # add dequantize node for output
    sm_output_quantized_idxs = observed_standalone_module.meta[
        "_observed_graph_module_attrs"
    ].standalone_module_output_quantized_idxs
    if len(sm_output_quantized_idxs) > 0:
        if sm_output_quantized_idxs[0] != 0:
            raise AssertionError(
                "Currently only quantized output idxs = [0] is supported"
            )

        # if it's non-empty, then it means the output is kept in quantized form
        # we'll just add a dequantize node after this node
        _insert_dequantize_node(node, model.graph)

    # TODO: allow convert_custom_config to override backend_config
    # for standalone module
    quantized_standalone_module = convert_fn(
        observed_standalone_module, backend_config=backend_config
    )
    parent_name, name = _parent_name(node.target)
    # update the modules dict
    setattr(modules[parent_name], name, quantized_standalone_module)
    modules[str(node.target)] = quantized_standalone_module