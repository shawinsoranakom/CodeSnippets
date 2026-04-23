def checkGraphModuleNodes(
        self,
        graph_module,
        expected_node=None,
        expected_node_occurrence=None,
        expected_node_list=None,
    ):
        """Check if GraphModule contains the target node
        Args:
            graph_module: the GraphModule instance we want to check
            expected_node, expected_node_occurrence, expected_node_list:
               see docs for checkGraphModeFxOp
        """
        nodes_in_graph = {}
        node_list = []
        modules = dict(graph_module.named_modules(remove_duplicate=False))
        for node in graph_module.graph.nodes:
            n = None
            if node.op == "call_function" or node.op == "call_method":
                n = NodeSpec(node.op, node.target)
            elif node.op == "call_module":
                n = NodeSpec(node.op, type(modules[node.target]))

            if n is not None:
                node_list.append(n)
                if n in nodes_in_graph:
                    nodes_in_graph[n] += 1
                else:
                    nodes_in_graph[n] = 1

        if expected_node is not None:
            self.assertTrue(
                expected_node in nodes_in_graph,
                "node:" + str(expected_node) + " not found in the graph module",
            )

        if expected_node_occurrence is not None:
            for expected_node, occurrence in expected_node_occurrence.items():
                if occurrence != 0:
                    self.assertTrue(
                        expected_node in nodes_in_graph,
                        "Check failed for node:" + str(expected_node) + " not found",
                    )
                    self.assertTrue(
                        nodes_in_graph[expected_node] == occurrence,
                        "Check failed for node:"
                        + str(expected_node)
                        + " Expected occurrence:"
                        + str(occurrence)
                        + " Found occurrence:"
                        + str(nodes_in_graph[expected_node]),
                    )
                else:
                    self.assertTrue(
                        expected_node not in nodes_in_graph,
                        "Check failed for node:"
                        + str(expected_node)
                        + " expected no occurrence but found",
                    )

        if expected_node_list is not None:
            cur_index = 0
            for n in node_list:
                if cur_index == len(expected_node_list):
                    return
                if n == expected_node_list[cur_index]:
                    cur_index += 1
            self.assertTrue(
                cur_index == len(expected_node_list),
                "Check failed for graph:"
                + self.printGraphModule(graph_module, print_str=False)
                + "Expected ordered list:"
                + str(expected_node_list),
            )