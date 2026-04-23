def find_first_unfusible(start_nodes: list[fx.Node], max_range: int) -> int:
        """
        Finds the first unfusible node in the chain of nodes starting from
        `start_nodes` and returns its position.
        """
        sorted_nodes: list[tuple[int, fx.Node, bool]] = []
        for n in start_nodes:
            heapq.heappush(sorted_nodes, (node_info.get_fw_order(n), n, True))

        while len(sorted_nodes) > 0:
            _, node, node_is_fusible = heapq.heappop(sorted_nodes)
            if not node_is_fusible:
                return node_info.get_fw_order(node)
            for user in node.users:
                if node_info.is_required_fw(user):
                    if node_info.get_fw_order(user) > max_range:
                        continue
                    val: tuple[int, fx.Node, bool] = (
                        node_info.get_fw_order(user),
                        user,
                        is_fusible(node, user),
                    )
                    if val not in sorted_nodes:
                        heapq.heappush(sorted_nodes, val)
        return max_range