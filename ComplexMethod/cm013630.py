def remove_bookend_non_compute_ops(self, partitions: list[Partition]) -> None:
        non_compute_ops = set(self.non_compute_ops)

        def is_non_compute_node(node: Node) -> bool:
            return (
                node.op == "call_function"
                and _get_qualified_name(node.target) in non_compute_ops  # type: ignore[arg-type]
            )

        # cache transparent nodes
        transparent_input_nodes: dict[Node, bool] = {}
        transparent_output_nodes: dict[Node, bool] = {}

        def is_transparent_input_node(
            node: Node, partition: set[Node], removed_nodes: set[Node]
        ) -> bool:
            if (
                node.op == "placeholder"
                or (node not in partition)
                or (node in removed_nodes)
            ):
                return True
            if node in transparent_input_nodes:
                return transparent_input_nodes[node]
            if is_non_compute_node(node):
                for input_n in node.all_input_nodes:
                    if not is_transparent_input_node(input_n, partition, removed_nodes):
                        transparent_input_nodes[node] = False
                        return False
                transparent_input_nodes[node] = True
                return True
            transparent_input_nodes[node] = False
            return False

        def is_transparent_output_node(
            node: Node, partition: set[Node], removed_nodes: set[Node]
        ) -> bool:
            if (
                node.op == "placeholder"
                or (node not in partition)
                or (node in removed_nodes)
            ):
                return True
            if node in transparent_output_nodes:
                return transparent_output_nodes[node]
            if is_non_compute_node(node):
                for output_n in node.users:
                    if not is_transparent_output_node(
                        output_n, partition, removed_nodes
                    ):
                        transparent_output_nodes[node] = False
                        return False
                transparent_output_nodes[node] = True
                return True
            transparent_output_nodes[node] = False
            return False

        for partition in partitions:
            # Note it's ok to use `set` here, since we are only query if a node
            # has been removed. We are NEVER going to iterate on nodes inside
            # the set.
            remove_node: set[Node] = set()
            for node in partition.nodes:
                if is_non_compute_node(node) and (
                    is_transparent_input_node(node, set(partition.nodes), remove_node)
                    or is_transparent_output_node(
                        node, set(partition.nodes), remove_node
                    )
                ):
                    remove_node.add(node)

            if len(remove_node) != 0:
                for node in remove_node:
                    partition.nodes.pop(node, None)