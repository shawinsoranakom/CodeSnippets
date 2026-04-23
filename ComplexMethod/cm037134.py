def __call__(self, graph: fx.Graph) -> None:
        count = 0

        # Map from input tensor node -> list of split nodes seen so far.
        split_nodes: dict[fx.Node, list[fx.Node]] = {}

        for node in graph.nodes:
            if not is_func(node, torch.ops.aten.split_with_sizes.default):
                continue
            if not all(is_func(user, operator.getitem) for user in node.users):
                continue

            arg_node, split_sizes = node.args[:2]

            if arg_node not in split_nodes:
                split_nodes[arg_node] = [node]
                continue

            # Find existing node with same split_sizes
            canonical = next(
                (
                    n
                    for n in split_nodes[arg_node]
                    if list(n.args[1]) == list(split_sizes)
                ),
                None,
            )
            if canonical is not None:
                node.replace_all_uses_with(canonical)
                graph.erase_node(node)
                count += 1
            else:
                split_nodes[arg_node].append(node)

        logger.debug("Coalesced %d duplicate split_with_sizes nodes", count)