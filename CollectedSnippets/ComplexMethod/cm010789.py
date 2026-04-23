def _recreate_psuedo_joint_graph(self) -> Graph:
        # Create a dictionary to store the dependencies of each node
        node_dependencies: dict[str, list[str]] = {
            node: [] for node in self.graph_nodes_in_order
        }
        for a, b in self.graph_edges:
            if a not in node_dependencies or b not in node_dependencies:
                raise ValueError(f"Edge ({a}, {b}) references a non-existent node.")
            node_dependencies[b].append(a)

        joint_graph = Graph()
        # Create nodes in the graph
        nodes: dict[str, Node] = {}
        for node_name in self.graph_nodes_in_order:
            input_nodes = [nodes[dep] for dep in node_dependencies[node_name]]
            if input_nodes:
                node = joint_graph.call_function(lambda *x: x, tuple(input_nodes))
                node.name = node_name
            else:
                node = joint_graph.placeholder(node_name)
            nodes[node_name] = node
        return joint_graph