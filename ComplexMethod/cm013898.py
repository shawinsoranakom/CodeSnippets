def _create_subgraph(
    region: Region,
    inds_with_external_users: list[int],
) -> tuple[
    torch.fx.Graph,
    list[OrderedSet[UsageIndex]],
    dict[UsageIndex, OrderedSet[int]],
    dict[int, dict[tuple[int, ...], int]],
]:
    subgraph: torch.fx.Graph = torch.fx.Graph()
    external_input_to_usages = _get_external_inputs(region)
    external_node_usages = list[OrderedSet[UsageIndex]]()
    region_to_subgraph_node = {}
    flattened_getitem_nodes: OrderedSet[Node] = OrderedSet()
    node_usage_to_tuple_elems: dict[UsageIndex, OrderedSet[int]] = {}

    for node, usage_indices in external_input_to_usages.items():
        # We don't handle tuples as inputs today
        if _is_tuple_node(node):
            # If a node is a tuple we will possibly create multiple placeholders for them
            # and track which nodes we won't copy into the subgraph because they are flattened away
            # Later, when replacing each region with this subgraph, we will create a getitem node
            # externally which will perform the flattening on the outer nodes.
            flattened_node_indices = _get_flattened_node_indices(node, region)
            for ind in flattened_node_indices:
                placeholder = subgraph.placeholder(
                    f"supgraph_input_{node.name}_flattened_{ind}"
                )
                region_to_subgraph_node[region[ind]] = placeholder
                flattened_getitem_nodes.add(region[ind])
            node_usage_to_tuple_elems[next(iter(usage_indices))] = (
                flattened_node_indices
            )
        else:
            placeholder = subgraph.placeholder(f"subgraph_input_{node.name}")
            region_to_subgraph_node[node] = placeholder

        external_node_usages.append(usage_indices)

    def map_arg(node: Node) -> Node:
        if node in region_to_subgraph_node:
            return region_to_subgraph_node[node]
        else:
            return node

    def copy_to_subgraph(node: Node) -> Node:
        subgraph_node = subgraph.node_copy(node, lambda old: map_arg(old))
        region_to_subgraph_node[node] = subgraph_node
        return subgraph_node

    output_list = []
    ind_to_tuple_spec = {}
    for ind, node in enumerate(region):
        if node not in flattened_getitem_nodes:
            subgraph_node = copy_to_subgraph(node)
            if ind in inds_with_external_users:
                # flatten tuple outputs by generating a getitem node tree
                if _is_tuple_node(node):
                    getitem_nodes, ind_to_tuple_spec[ind] = _create_getitem_nodes(
                        node, subgraph_node, subgraph
                    )
                    output_list.extend(getitem_nodes)
                else:
                    output_list.append(subgraph_node)

    subgraph.output(tuple(output_list))

    return subgraph, external_node_usages, node_usage_to_tuple_elems, ind_to_tuple_spec