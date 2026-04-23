def _run_symbolic_function(
    graph: _C.Graph,
    block: _C.Block,
    node: _C.Node,
    inputs: Any,
    env: dict[_C.Value, _C.Value],
    values_in_env: set[_C.Value],
    new_nodes: list[_C.Node],
    operator_export_type=_C_onnx.OperatorExportTypes.ONNX,
) -> _C.Value | Sequence[_C.Value | None] | None:
    """Runs a symbolic function.

    The function is used in C++ to export the node to ONNX.

    Returns:
        A single or a tuple of Values.
        None when the node gets cloned as is into the new graph.
    """

    opset_version = GLOBALS.export_onnx_opset_version

    # See Note [Export inplace]
    node_kind = node.kind()
    if node_kind.endswith("_"):
        # Treat relu_ -> relu; add_ -> add etc.
        ns_op_name = node_kind[:-1]
    else:
        ns_op_name = node_kind

    namespace, op_name = jit_utils.parse_node_kind(ns_op_name)

    graph_context = jit_utils.GraphContext(
        graph=graph,
        block=block,
        opset=opset_version,
        original_node=node,
        params_dict=_params_dict,
        env=env,
        values_in_env=values_in_env,
        new_nodes=new_nodes,
    )

    # Direct ATen export requested
    if _should_aten_fallback(ns_op_name, opset_version, operator_export_type):
        attrs = {
            k + "_" + node.kindOf(k)[0]: symbolic_helper._node_get(node, k)
            for k in node.attributeNames()
        }
        outputs = node.outputsSize()
        attrs["outputs"] = outputs
        return graph_context.aten_op(
            op_name,
            *inputs,
            overload_name=_get_aten_op_overload_name(node),
            **attrs,
        )

    try:
        domain = namespace
        symbolic_function_name = f"{domain}::{op_name}"

        symbolic_function_group = registration.registry.get_function_group(
            symbolic_function_name
        )
        if symbolic_function_group is not None:
            symbolic_fn = symbolic_function_group.get(opset_version)
            if symbolic_fn is not None:
                # TODO Wrap almost identical attrs assignment or comment the difference.
                attrs = {
                    k: symbolic_helper._node_get(node, k) for k in node.attributeNames()
                }
                return symbolic_fn(graph_context, *inputs, **attrs)

        attrs = {
            k + "_" + node.kindOf(k)[0]: symbolic_helper._node_get(node, k)
            for k in node.attributeNames()
        }
        if namespace == "onnx":
            # Clone node to trigger ONNX shape inference
            return graph_context.op(
                op_name, *inputs, **attrs, outputs=node.outputsSize()
            )  # type: ignore[attr-defined]

        raise errors.UnsupportedOperatorError(
            symbolic_function_name,
            opset_version,
            symbolic_function_group.get_min_supported()
            if symbolic_function_group
            else None,
        )

    except RuntimeError:
        if operator_export_type == _C_onnx.OperatorExportTypes.ONNX_FALLTHROUGH:
            return None
        elif operator_export_type == _C_onnx.OperatorExportTypes.ONNX_ATEN_FALLBACK:
            # Emit ATen op for non-Caffe2 builds when `operator_export_type==ONNX_ATEN_FALLBACK`
            attrs = {
                k + "_" + node.kindOf(k)[0]: symbolic_helper._node_get(node, k)
                for k in node.attributeNames()
            }
            return graph_context.aten_op(
                op_name,
                *inputs,
                overload_name=_get_aten_op_overload_name(node),
                **attrs,
            )
        raise
    except TypeError as e:
        # Handle the specific case where we didn't successfully dispatch.
        # Otherwise, the backtrace will have the clues you need.
        e.args = (f"{e.args[0]} \n(Occurred when translating {op_name}).",)
        raise