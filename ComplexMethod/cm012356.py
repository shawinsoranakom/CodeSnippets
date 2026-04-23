def reorder_nodes(graph: Graph) -> Graph:
    """
    Create a new graph to be like:
    1. all nodes run before `chunking_subgraph_nodes`
    2. all nodes in `chunking_subgraph_nodes`
    3. all nodes run after `chunking_subgraph_nodes`

    Return a new graph so it's easier to fallback.
    """
    from .applier import is_chunking_subgraph_input

    # `pre_chunking_nodes` are all nodes that only depends on
    # nodes inside `pre_chuning_nodes`
    pre_chunking_nodes: OrderedSet[Node] = OrderedSet()

    for node in graph.nodes:
        if node.op == "placeholder" or is_chunking_subgraph_input(node):
            # these nodes have chunking meta but they should be placed
            # before we do chunking
            pre_chunking_nodes.add(node)

        if get_chunking_meta(node) is not None:
            continue
        if all(arg in pre_chunking_nodes for arg in get_args_of_node_type(node)):
            pre_chunking_nodes.add(node)

    post_chunking_nodes = []

    def _copy_node(typestr: str, node: Node) -> None:
        if log.isEnabledFor(logging.DEBUG):
            fake_tensor = get_fake_tensor_from_node_arg(node)
            shape = list(fake_tensor.shape) if fake_tensor is not None else "?"
            log.debug(" - %s: %s %s", typestr, shape, node.format_node())
        env[node] = new_graph.node_copy(node, lambda x: env[x])

    # add pre_chunking_nodes
    new_graph = Graph()
    env: dict[Node, Node] = {}
    for node in pre_chunking_nodes:
        _copy_node("prechunking", node)

    # add nodes in the chunking subgraph
    for node in graph.nodes:
        if node in pre_chunking_nodes:
            continue
        elif get_chunking_meta(node):
            _copy_node("chunking", node)
        else:
            post_chunking_nodes.append(node)

    for node in post_chunking_nodes:
        _copy_node("postchuking", node)

    assert graph._len == new_graph._len
    new_graph.eliminate_dead_code()
    new_graph.lint()

    # Need replace the scale_by node in the chunking meta with the new node
    for node in new_graph.nodes:
        meta = get_chunking_meta(node)
        if meta and meta.scale_by is not None:
            meta.scale_by = env[meta.scale_by]

    return new_graph