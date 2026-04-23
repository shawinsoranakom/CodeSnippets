def _translate_fx_graph(
    fx_graph: torch.fx.Graph,
    model: ir.Model,
    *,
    graph_like: ir.Graph | ir.Function,
    owned_graphs: Mapping[str, ir.Function],
    lower: Literal["at_conversion", "none"],
    registry: _registration.ONNXRegistry,
) -> dict[str, ir.Value | Sequence[ir.Value]]:
    """Translate a submodule to an ONNX function.

    Any functions used by the traced functions will be added to the model.

    Args:
        fx_graph: The FX graph module to translate.
        model: The ONNX model at construction.
        current_scope: The current name scope of the submodule, excluding the current module name.
            E.g. "true_graph_0.false_graph_0".
        graph_name: The name of the submodule. E.g. "true_graph_0".
        graph: The ONNX graph at construction.
        owned_graphs: The subgraphs owned by the current graph.
        lower: The lowering strategy to use.
        registry: The registry of all aten to ONNX decomposition functions.

    Returns:
        A mapping of FX node names to their produced ONNX ``Value``.
    """
    node_name_to_values: dict[str, ir.Value | Sequence[ir.Value]] = {}
    # The reason we need node_name_to_local_functions in addition to owned_graphs
    # is because the get_attr nodes may assign a different name than the GraphModule name
    # to the subgraph. This is not typical but is valid Python.
    node_name_to_local_functions: dict[str, ir.Function] = {}
    constant_farm: dict[Any, ir.Value] = {}
    opset = _get_onnxscript_opset(registry.opset_version)

    for node in fx_graph.nodes:
        logger.debug(
            "%s", (node.name, node.args, node.target, node.op, node.type, node.kwargs)
        )
        try:
            if node.op == "placeholder":
                _handle_placeholder_node(
                    node,
                    node_name_to_values,
                    graph_like=graph_like,
                    lower=lower,
                    opset=opset,
                )
            elif node.op == "call_function":
                if lower == "at_conversion":
                    _handle_call_function_node_with_lowering(
                        model,
                        node,
                        node_name_to_values,
                        graph_like=graph_like,
                        constant_farm=constant_farm,
                        registry=registry,
                        opset=opset,
                        node_name_to_local_functions=node_name_to_local_functions,
                    )
                else:
                    # No lowering
                    _handle_call_function_node(graph_like, node, node_name_to_values)
            elif node.op == "get_attr":
                _handle_get_attr_node(
                    node,
                    owned_graphs=owned_graphs,
                    node_name_to_local_functions=node_name_to_local_functions,
                )
            elif node.op == "output":
                _handle_output_node(
                    node,
                    node_name_to_values,
                    graph_like=graph_like,
                )
        except Exception as e:
            raise _errors.ConversionError(
                f"Error when translating node {node.format_node()}. See the stack trace for more information."
            ) from e
    return node_name_to_values