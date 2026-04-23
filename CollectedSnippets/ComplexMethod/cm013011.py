def _find_onnxscript_op(
    graph_proto,
    included_node_func: set[str],
    custom_opsets: Mapping[str, int],
    onnx_function_list: list,
):
    """Recursively iterate ModelProto to find ONNXFunction op as it may contain control flow Op."""
    for node in graph_proto.node:
        node_kind = node.domain + "::" + node.op_type
        # Recursive needed for control flow nodes: IF/Loop which has inner graph_proto
        for attr in node.attribute:
            if attr.g is not None:
                _find_onnxscript_op(
                    attr.g, included_node_func, custom_opsets, onnx_function_list
                )
        # Only custom Op with ONNX function and aten with symbolic_fn should be found in registry
        onnx_function_group = registration.registry.get_function_group(node_kind)
        # Ruled out corner cases: onnx/prim in registry
        if (
            node.domain
            and not jit_utils.is_aten(node.domain)
            and not jit_utils.is_prim(node.domain)
            and not jit_utils.is_onnx(node.domain)
            and onnx_function_group is not None
            and node_kind not in included_node_func
        ):
            specified_version = custom_opsets.get(node.domain, 1)
            onnx_fn = onnx_function_group.get(specified_version)
            if onnx_fn is not None:
                if hasattr(onnx_fn, "to_function_proto"):
                    onnx_function_proto = onnx_fn.to_function_proto()  # type: ignore[attr-defined]
                    onnx_function_list.append(onnx_function_proto)
                    included_node_func.add(node_kind)
                continue

            raise errors.UnsupportedOperatorError(
                node_kind,
                specified_version,
                onnx_function_group.get_min_supported()
                if onnx_function_group
                else None,
            )
    return onnx_function_list, included_node_func