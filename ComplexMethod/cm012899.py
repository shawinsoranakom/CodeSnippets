def _get_reference_quantized_lstm_module(
    observed_lstm: torch.ao.nn.quantizable.LSTM,
    backend_config: BackendConfig | None = None,
) -> torch.ao.nn.quantized.LSTM:
    """
    Return a `torch.ao.nn.quantized.LSTM` created from a `torch.ao.nn.quantizable.LSTM`
    with observers or fake quantizes inserted through `prepare_fx`, e.g. from
    `_get_lstm_with_individually_observed_parts`.

    This is meant to be used to convert an observed module to a quantized module in the
    custom module flow.

    Args:
        `observed_lstm`: a `torch.ao.nn.quantizable.LSTM` observed through `prepare_fx`
        `backend_config`: BackendConfig to use to produce the reference quantized model

    Return:
        A reference `torch.ao.nn.quantized.LSTM` module.
    """
    quantized_lstm = torch.ao.nn.quantized.LSTM(
        observed_lstm.input_size,
        observed_lstm.hidden_size,
        observed_lstm.num_layers,
        observed_lstm.bias,
        observed_lstm.batch_first,
        observed_lstm.dropout,
        observed_lstm.bidirectional,
    )

    for i, layer in enumerate(quantized_lstm.layers):
        cell = copy.deepcopy(observed_lstm.layers.get_submodule(str(i)).layer_fw.cell)  # type: ignore[union-attr]
        cell = convert_to_reference_fx(cell, backend_config=backend_config)  # type: ignore[arg-type]
        if not isinstance(cell, torch.fx.GraphModule):
            raise AssertionError("cell must be converted to a torch.fx.GraphModule")
        # HACK: Manually remove input quantize nodes and output dequantize nodes,
        # since custom modules expect quint8 inputs and outputs for now. Note that
        # this functionality is supposedly handled through PrepareCustomConfig's
        # `set_input_quantized_indexes` and `set_output_quantized_indexes`, but that
        # API doesn't currently handle tuple inputs and outputs, so we have to do
        # this manually for now. In the future we should (1) relax the restriction
        # on custom module input/output dtypes, and (2) expand support for complex
        # input/output structures.
        for node in cell.graph.nodes:
            if node.target is torch.quantize_per_tensor:
                arg = node.args[0]
                # Remove quantize(x), quantize(hidden[0]), and quantize(hidden[1])
                if arg.target == "x" or (
                    arg.target is operator.getitem and arg.args[0].target == "hidden"
                ):
                    with cell.graph.inserting_before(node):
                        node.replace_all_uses_with(arg)
                        cell.graph.erase_node(node)
            if node.target == "output":
                # Remove all dequantize nodes in the output tuple
                for arg in node.args[0]:
                    with cell.graph.inserting_before(node):
                        node.replace_input_with(arg, arg.args[0])
        cell.graph.eliminate_dead_code()
        cell.recompile()
        layer.layer_fw.cell = cell  # type: ignore[union-attr]
    return quantized_lstm