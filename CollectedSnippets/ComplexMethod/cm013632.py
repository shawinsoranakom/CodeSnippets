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