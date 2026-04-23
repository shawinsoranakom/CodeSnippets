def draw_buffers(
    nodes: list[BaseSchedulerNode],
    print_graph: bool = False,
    fname: str | None = None,
) -> None:
    """
    Draw a graph in fname.svg.
    """
    if not has_dot():
        log.warning("draw_buffers() requires `graphviz` package")
        return

    if fname is None:
        fname = get_graph_being_compiled()

    graph = create_fx_from_snodes(nodes)

    for node in graph.nodes:
        if "fusion_meta" not in node.meta:
            continue
        group = node.meta["fusion_meta"].group
        if isinstance(group, tuple):
            if isinstance(group[1], int):
                group = (group[1],)
            else:
                group = group[1]
        elif isinstance(group, str):
            # extern / template / nop nodes store a string like "extern"
            # as the group instead of a shape tuple.  Extract the real
            # output shape from the scheduler node's first output buffer.
            try:
                snode = node.meta["fusion_meta"].snode
                size = snode.get_outputs()[0].node.maybe_get_size()
                group = tuple(size) if size else ()
            except Exception:
                group = ()

        # gather meta data
        dtype = None
        if isinstance(node, ir.ComputedBuffer):
            dtype = node.data.dtype

        metadata = TensorMetadata(group, dtype, None, None, None, None, None)  # type: ignore[arg-type]

        node.meta["tensor_meta"] = metadata

    if print_graph:
        print(graph)

    gm = GraphModule({}, graph)
    legalize_graph(gm)
    gm.graph.lint()
    draw_graph(
        gm, fname, clear_meta=False, dot_graph_shape=config.trace.dot_graph_shape
    )