def _rewrite_scalar_gather(model) -> bool:
    """Rewrite Gather(data, scalar_idx) as Gather(data, [scalar_idx]) + Squeeze.

    Only touches Gather nodes whose index is a rank-0 int64 constant or
    initializer; everything else passes through unchanged. The rewrite
    is semantically identical — indices get an added leading axis, the
    Squeeze removes it after the gather.
    """
    from onnx import numpy_helper, helper, TensorProto

    graph = model.graph

    # Opset 13 moved Squeeze's axes from attribute to input.
    opset = next(
        (o.version for o in model.opset_import if o.domain in ("", "ai.onnx")),
        11,
    )

    const_values = {}
    for n in graph.node:
        if n.op_type == "Constant":
            for a in n.attribute:
                if a.name == "value":
                    const_values[n.output[0]] = a.t
    init_values = {i.name: i for i in graph.initializer}

    def scalar_int64(name):
        """Return int value if `name` resolves to a rank-0 int64 constant, else None."""
        tensor = const_values.get(name) or init_values.get(name)
        if tensor is None or tensor.data_type != TensorProto.INT64:
            return None
        arr = numpy_helper.to_array(tensor)
        return int(arr) if arr.ndim == 0 else None

    rewrote = 0
    new_nodes = []
    for n in graph.node:
        if n.op_type == "Gather":
            val = scalar_int64(n.input[1])
            if val is not None:
                axis = next((a.i for a in n.attribute if a.name == "axis"), 0)
                idx_1d_name = f"{n.input[1]}_1d_{rewrote}"
                idx_const = helper.make_node(
                    "Constant",
                    inputs=[],
                    outputs=[idx_1d_name],
                    value=helper.make_tensor(idx_1d_name, TensorProto.INT64, [1], [val]),
                )
                gather_out = f"{n.output[0]}_pre_squeeze_{rewrote}"
                new_gather = helper.make_node(
                    "Gather",
                    inputs=[n.input[0], idx_1d_name],
                    outputs=[gather_out],
                    name=n.name,
                    axis=axis,
                )
                if opset < 13:
                    squeeze = helper.make_node(
                        "Squeeze",
                        inputs=[gather_out],
                        outputs=[n.output[0]],
                        name=(n.name or "gather") + "_squeeze",
                        axes=[axis],
                    )
                    new_nodes.extend([idx_const, new_gather, squeeze])
                else:
                    axes_name = f"{idx_1d_name}_sq_axes"
                    axes_const = helper.make_node(
                        "Constant",
                        inputs=[],
                        outputs=[axes_name],
                        value=helper.make_tensor(axes_name, TensorProto.INT64, [1], [axis]),
                    )
                    squeeze = helper.make_node(
                        "Squeeze",
                        inputs=[gather_out, axes_name],
                        outputs=[n.output[0]],
                        name=(n.name or "gather") + "_squeeze",
                    )
                    new_nodes.extend([idx_const, axes_const, new_gather, squeeze])
                rewrote += 1
                continue
        new_nodes.append(n)

    if rewrote == 0:
        return False

    del graph.node[:]
    graph.node.extend(new_nodes)
    return True