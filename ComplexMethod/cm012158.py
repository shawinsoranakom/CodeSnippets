def all_reach_via_pointwise_with_no_other_inputs(
        src: torch.fx.Node,
        dst: torch.fx.Node,
    ) -> tuple[bool, OrderedSet[torch.fx.Node]]:
        """
        check whether every user path from src reaches dst via pointwise nodes,
        with no other input nodes for the intermediates and dst;
        return
        (1) the Boolean value
        (2) the subgraph node set including src and dst (which only makes sense when the Boolean value is True)
        """
        visited = OrderedSet[torch.fx.Node]()
        input_counter: dict[torch.fx.Node, int] = {}

        all_reachable = True
        queue = deque([src])
        while queue:
            node = queue.popleft()
            if node not in visited:
                if node is dst:
                    visited.add(node)
                elif (node is src) or is_pointwise_node(node):
                    for user in node.users:
                        # for nodes other than dst, bookkeep their users' input counts
                        if user not in input_counter:
                            input_counter[user] = len(user.all_input_nodes)
                        input_counter[user] -= 1
                        # continue BFS
                        queue.append(user)
                    visited.add(node)
                else:
                    all_reachable = False
                    break

        return (
            all_reachable and all(count == 0 for count in input_counter.values()),
            visited,
        )