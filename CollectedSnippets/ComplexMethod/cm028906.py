def _decompose_reflect_pad(model) -> bool:
    """Rewrite Pad(reflect) as Slice+Concat sequences CoreML can handle."""
    from onnx import numpy_helper, helper

    graph = model.graph
    inits = {init.name: numpy_helper.to_array(init) for init in graph.initializer}

    reflect_pads = []
    for node in graph.node:
        if node.op_type == "Pad":
            mode = "constant"
            for attr in node.attribute:
                if attr.name == "mode":
                    mode = attr.s.decode()
            if mode == "reflect" and len(node.input) > 1 and node.input[1] in inits:
                reflect_pads.append(node)

    if not reflect_pads:
        return False

    existing_names = {i.name for i in graph.initializer}

    def ensure_const(name, value):
        if name not in existing_names:
            graph.initializer.append(
                numpy_helper.from_array(np.array(value, dtype=np.int64), name=name)
            )
            existing_names.add(name)

    ensure_const("_rp_ax2", [2])
    ensure_const("_rp_ax3", [3])

    max_pad = 0
    for node in reflect_pads:
        pads = inits[node.input[1]].tolist()
        max_pad = max(max_pad, int(pads[2]), int(pads[3]))

    for v in range(1, max_pad + 2):
        ensure_const(f"_rp_p{v}", [v])
        ensure_const(f"_rp_n{v}", [-v])

    _counter = [0]

    def uid():
        _counter[0] += 1
        return _counter[0]

    pad_ids = {id(n) for n in reflect_pads}
    pad_init_names = set()

    new_nodes = []
    for node in graph.node:
        if id(node) not in pad_ids:
            new_nodes.append(node)
            continue

        pads = inits[node.input[1]].tolist()
        h_pad, w_pad = int(pads[2]), int(pads[3])

        for inp in node.input[1:]:
            if inp in inits:
                pad_init_names.add(inp)

        current = node.input[0]

        if h_pad > 0:
            top = []
            for i in range(h_pad, 0, -1):
                name = f"_rp_t{uid()}"
                new_nodes.append(helper.make_node(
                    "Slice",
                    inputs=[current, f"_rp_p{i}", f"_rp_p{i+1}", "_rp_ax2"],
                    outputs=[name],
                ))
                top.append(name)

            bot = []
            for i in range(1, h_pad + 1):
                name = f"_rp_b{uid()}"
                new_nodes.append(helper.make_node(
                    "Slice",
                    inputs=[current, f"_rp_n{i+1}", f"_rp_n{i}", "_rp_ax2"],
                    outputs=[name],
                ))
                bot.append(name)

            h_out = f"_rp_h{uid()}"
            new_nodes.append(helper.make_node(
                "Concat", inputs=top + [current] + bot, outputs=[h_out], axis=2
            ))
            current = h_out

        if w_pad > 0:
            left = []
            for i in range(w_pad, 0, -1):
                name = f"_rp_l{uid()}"
                new_nodes.append(helper.make_node(
                    "Slice",
                    inputs=[current, f"_rp_p{i}", f"_rp_p{i+1}", "_rp_ax3"],
                    outputs=[name],
                ))
                left.append(name)

            right = []
            for i in range(1, w_pad + 1):
                name = f"_rp_r{uid()}"
                new_nodes.append(helper.make_node(
                    "Slice",
                    inputs=[current, f"_rp_n{i+1}", f"_rp_n{i}", "_rp_ax3"],
                    outputs=[name],
                ))
                right.append(name)

            new_nodes.append(helper.make_node(
                "Concat",
                inputs=left + [current] + right,
                outputs=[node.output[0]],
                axis=3,
            ))
        elif h_pad > 0:
            new_nodes.append(helper.make_node(
                "Identity", inputs=[current], outputs=[node.output[0]]
            ))

    # Remove old Pad initializers
    clean_inits = [i for i in graph.initializer if i.name not in pad_init_names]
    del graph.initializer[:]
    graph.initializer.extend(clean_inits)

    del graph.node[:]
    graph.node.extend(new_nodes)
    return True