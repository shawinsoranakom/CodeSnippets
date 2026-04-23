def _decompose_split(model) -> bool:
    """Rewrite Split(axis=1) as Slice pairs that CoreML can handle.

    CoreML's EP doesn't support the ONNX ``Split`` op, causing partition
    boundaries in models that use channel-wise splits (e.g. GFPGAN's SFT
    modulation layers).  Each Split with two outputs becomes two Slice ops.
    """
    from onnx import numpy_helper, helper

    graph = model.graph

    splits = []
    for node in graph.node:
        if node.op_type == "Split":
            axis = 0
            split_sizes = []
            for attr in node.attribute:
                if attr.name == "axis":
                    axis = attr.i
                if attr.name == "split":
                    split_sizes = list(attr.ints)
            if axis == 1 and len(split_sizes) == 2 and len(node.output) == 2:
                splits.append((node, split_sizes))

    if not splits:
        return False

    existing = {i.name for i in graph.initializer}

    def ensure_const(name, value):
        if name not in existing:
            graph.initializer.append(
                numpy_helper.from_array(np.array(value, dtype=np.int64), name=name)
            )
            existing.add(name)

    ensure_const("_sp_ax1", [1])

    # Collect all needed boundary constants
    for _, (a, b) in splits:
        ensure_const(f"_sp_s0", [0])
        ensure_const(f"_sp_s{a}", [a])
        ensure_const(f"_sp_s{a + b}", [a + b])

    split_ids = {id(node) for node, _ in splits}
    replacements = {}
    for node, (a, b) in splits:
        slice0 = helper.make_node(
            "Slice",
            inputs=[node.input[0], "_sp_s0", f"_sp_s{a}", "_sp_ax1"],
            outputs=[node.output[0]],
        )
        slice1 = helper.make_node(
            "Slice",
            inputs=[node.input[0], f"_sp_s{a}", f"_sp_s{a + b}", "_sp_ax1"],
            outputs=[node.output[1]],
        )
        replacements[id(node)] = [slice0, slice1]

    new_nodes = []
    for node in graph.node:
        if id(node) in split_ids:
            new_nodes.extend(replacements[id(node)])
        else:
            new_nodes.append(node)

    del graph.node[:]
    graph.node.extend(new_nodes)
    return True