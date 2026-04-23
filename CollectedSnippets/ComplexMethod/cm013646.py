def fuse_as_graphmodule(
    gm: GraphModule,
    nodes: NodeList,
    module_name: str,
    partition_lookup_table: dict[Node, int | None] | None = None,
    *,
    always_return_tuple: bool = False,
) -> tuple[GraphModule, tuple[Node, ...], tuple[Node, ...]]:
    """
    Fuse nodes in graph_module into a GraphModule.

    Args:
        gm (GraphModule): target graph_module

        nodes (List[Node]): list of nodes in `gm` to fuse, where the node must be topologically sorted

        module_name: class name for the fused GraphModule

        partition_lookup_table (Optional[Dict[Node, None]]): optional dict of nodes to speed up lookup

        always_return_tuple (bool): whether to always return a tuple, even if there is only one output

    Returns:
        fused_gm (GraphModule): fused graph module, where its node is a copy of `nodes` in `gm`

        original_inputs (Tuple[Node, ...]): input nodes to `nodes` in original `gm`

        original_outputs (Tuple[Node, ...]): consumer nodes of `nodes` in original `gm`

    """

    # assumption: nodes are already sorted in topo order

    for node in nodes:
        if node.graph.owning_module is not gm:
            raise AssertionError(
                f"{node} doesn't belong to passed in graph module {gm._get_name()}"
            )
        if node._erased:
            raise AssertionError(f"{node} has been removed from owning graph")
        if node not in gm.graph._find_nodes_lookup_table:
            raise AssertionError(
                f"{node} is not found in graph module {gm._get_name()}"
            )

    # validates partition doesn't introduce dependency circles in the graph
    if not validate_partition(nodes):
        raise AssertionError("Invalid partition, found dependency cycles")

    # if no dict of partition nodes is provided, reconstruct it by nodes list to reduce lookup time
    if partition_lookup_table is None:
        partition_lookup_table = dict.fromkeys(nodes)

    subgraph = Graph()

    node_to_placeholder: dict[
        Node, Node
    ] = {}  # mapping of nodes from old graph to placeholder in new graph
    node_map: dict[Node, Node] = {}  # mapping of nodes from old graph to new graph

    # handles inputs through graph.node_copy's arg_transform functions
    def remap_inputs(x: Node) -> Node:
        if x.op == "get_attr":
            # TODO: do we really need copy the get_attr node into the graph?
            # do something here
            pass

        if x in partition_lookup_table:
            # x is inside subgraph, return the copied node
            # the node should have been copied already, as we are copying graph in the topological order
            return node_map[x]

        if x not in node_to_placeholder:
            # x is not in subgraph, create a new placeholder for subgraph
            placeholder_node = subgraph.placeholder(x.name, type_expr=x.type)
            # copy all meta fields, even if some fields might be irrelevant for the placeholder node
            placeholder_node.meta = copy.copy(x.meta)
            node_to_placeholder[x] = placeholder_node

        return node_to_placeholder[x]

    # copy nodes in topological order
    for node in nodes:
        new_node = subgraph.node_copy(node, remap_inputs)
        node_map[node] = new_node

    # handles outputs
    output_mapping: dict[Node, Node] = {}  # mapping from old output to new outputs

    for node in nodes:
        for user_node in node.users:
            if user_node not in partition_lookup_table:
                # external user node, need to expose as an output
                output_mapping[node] = node_map[node]

    # outs contain nodes in the new subgraph
    outs = tuple(output_mapping.values())

    if always_return_tuple:
        # always return a tuple, even if there is only one output
        subgraph.output(outs)
    else:
        # If there's a single output then return it directly, otherwise return a tuple.
        subgraph.output(outs[0] if len(outs) == 1 else outs)

    # lint to ensure correctness
    subgraph.lint()  # type: ignore[no-untyped-call]
    fused_gm: GraphModule
    fused_gm, _ = lift_subgraph_as_module(
        gm, subgraph, comp_name="", class_name=module_name
    )

    # sub_gm's input nodes in the original module
    original_inputs: tuple[Node, ...] = tuple(node_to_placeholder.keys())

    # sub_gm's outputs node in the original module
    original_outputs: tuple[Node, ...] = tuple(output_mapping.keys())

    return fused_gm, original_inputs, original_outputs