def _handle_call_function_node_with_lowering(
    model: ir.Model,
    node: torch.fx.Node,
    node_name_to_values: dict[str, ir.Value | Sequence[ir.Value]],
    *,
    graph_like: ir.Graph | ir.Function,
    constant_farm: dict[Any, ir.Value],
    registry: _registration.ONNXRegistry,
    opset: onnxscript.values.Opset,
    node_name_to_local_functions: dict[str, ir.Function],
) -> None:
    """Translate a call_function node to an ONNX node.

    Args:
        model: The ONNX model at construction.
        node: The FX node to translate.
        node_name_to_values: A mapping of FX node names to their produced ONNX ``Value``.
        graph_like: The current ONNX graph at construction.
            Must add nodes to this graph because it can be a subgraph that is currently being constructed.
        constant_farm: A mapping of constant values to existing ONNX ``Value``s.
        registry: The registry of all aten to ONNX decomposition functions.
        opset: The ONNX Script opset object for constructing ONNX nodes.
        node_name_to_local_functions: A mapping of subgraph names to the corresponding ONNX functions.
    """
    if node.target is operator.getitem:
        source = node.all_input_nodes[0]
        source_outputs = node_name_to_values[source.name]
        if isinstance(source_outputs, Sequence):
            _handle_getitem_node(node, node_name_to_values)
            return
        else:
            # `source_outputs` is a sequence(tensor()) value and we need to
            # use SequenceAt to get the value. This is handled by torchlib
            pass

    # Map FX inputs to ONNX inputs and fill optional inputs.
    # torch_args and torch_kwargs are for op-level validation
    fx_args = node.args
    fx_kwargs = node.kwargs

    # Replace the input FX nodes with ONNX values
    onnx_args = [
        _convert_fx_arg_to_onnx_arg(
            input_, node_name_to_values, node_name_to_local_functions
        )
        for input_ in fx_args
    ]

    onnx_kwargs = {}
    for key, value in fx_kwargs.items():
        onnx_kwargs[key] = _convert_fx_arg_to_onnx_arg(
            value, node_name_to_values, node_name_to_local_functions
        )
        if key == "dtype" and onnx_kwargs[key] is None:
            # Set dtype to -1 if it is None
            # TODO(justinchuby): Maybe keep it as None?
            onnx_kwargs[key] = -1

    if _is_onnx_op(node.target):
        # Handle torch.ops.onnx.* ops. These ops can be directly added to the graph
        op_type, opset_version = _parse_onnx_op(node.target)  # type: ignore[arg-type]
        # If final inputs are None, strip them from the node inputs
        for input_ in reversed(onnx_args):
            if input_ is not None:
                break
            onnx_args.pop()
        onnx_node = ir.Node(
            "",
            op_type,
            onnx_args,
            ir.convenience.convert_attributes(onnx_kwargs),
            name=node.name,
            num_outputs=len(node.target._schema.returns),  # type: ignore[union-attr]
            version=opset_version,
        )
        # Store the single node in a list to be consistent with the rest of the code for further processing
        onnx_nodes = [onnx_node]
        if len(onnx_node.outputs) == 1:
            outputs = onnx_node.outputs[0]
        else:
            outputs = onnx_node.outputs  # type: ignore[assignment]
    else:
        # Find the matching ONNX overload for the node
        # TODO: Log the message here to expose false positives
        onnx_function, message = _dispatching.dispatch(node, registry)

        if onnx_function is None:
            raise _errors.DispatchError(
                f"No ONNX function found for {node.target!r}. Failure message: {message}"
            )

        with onnxscript.evaluator.default_as(
            tracer := _building.OpRecorder(opset, constant_farm)
        ):
            global current_tracer
            current_tracer = tracer
            try:
                outputs = onnx_function(*onnx_args, **onnx_kwargs)
            except Exception as e:
                raise _errors.GraphConstructionError(
                    f"Error when calling function '{onnx_function}' with args '{onnx_args}' and kwargs '{onnx_kwargs}'"
                ) from e
            finally:
                current_tracer = None

        # Add the defined functions to the model
        for identifier, onnxscript_function in tracer.functions.items():
            if identifier in model.functions:
                continue
            if isinstance(onnxscript_function, ir.Function):
                ir_function = onnxscript_function
            else:
                # TODO: Get IR function directly when onnxscript is updated
                proto = onnxscript_function.to_function_proto()
                ir_function = ir.serde.deserialize_function(proto)
            model.functions[identifier] = ir_function
            # Opset imports are added to the model in the final add_opset_imports pass

        onnx_nodes = tracer.nodes
        del tracer  # tracer is no longer needed

    # NOTE: Instead of using the output names from node.target._schema,
    # we always use the index if there are more than one outputs so the
    # names can be programmatically reconstructed. This is useful for
    # comparing values from the ONNX graph with those from the FX graph.
    #
    # When there are multiple outputs, the output names will be
    # node_name__0, node_name__1, etc.
    if isinstance(outputs, Sequence):
        _set_shape_types(outputs, node.meta["val"], complex_to_float=True)
        node_name_to_values[node.name] = outputs
        for i, output in enumerate(outputs):
            output.name = f"{node.name}__{i}"
            # Set the name of the producing node using the value name for correspondence
            producer = output.producer()
            if producer is not None:
                producer.name = f"node_{output.name}"
    else:
        _set_shape_type(outputs, node.meta["val"], complex_to_float=True)
        node_name_to_values[node.name] = outputs
        outputs.name = node.name
        producer = outputs.producer()
        if producer is not None:
            producer.name = f"node_{outputs.name}"

    for ir_node in onnx_nodes:
        ir_node.meta["node"] = node
        # Record the nn.Module stack for the node
        _set_node_metadata(node, ir_node)

    # Add the traced nodes to the current graph
    # Must add nodes to this graph, not model.graph, because it can be a subgraph that is currently being constructed
    graph_like.extend(onnx_nodes)