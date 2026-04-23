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