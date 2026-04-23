def starter_nodes(self) -> tuple[NodeSet, NodeSet]:
        """
        Finds nodes that consume module inputs or get_attr nodes.
        """
        starter_cpu_nodes: NodeSet = set()
        starter_acc_nodes: NodeSet = set()
        for node in self.module.graph.nodes:
            # edge case, call_function, but with no dependencies
            if node.op == "call_function" and len(node.all_input_nodes) == 0:
                if node in self.acc_nodes:
                    starter_acc_nodes.add(node)
                else:
                    starter_cpu_nodes.add(node)

            if node.op not in {"placeholder", "get_attr"}:
                continue

            for user in node.users:
                if user in self.acc_nodes:
                    starter_acc_nodes.add(user)
                else:
                    starter_cpu_nodes.add(user)

        return starter_cpu_nodes, starter_acc_nodes