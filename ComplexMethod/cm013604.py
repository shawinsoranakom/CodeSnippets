def reduce_acc_nodes_non_tensor_output(self) -> None:
        """
        Excludes nodes from ACC supported set that produce non-tensor
        outputs and have downstream CPU nodes.
        """
        while True:
            new_cpu_nodes: NodeList = []

            for acc_node in self.acc_nodes:
                if is_node_output_tensor(acc_node):
                    continue
                for user in acc_node.users:
                    if user not in self.acc_nodes:
                        new_cpu_nodes.append(acc_node)
                        self.tracker.add(
                            acc_node, "acc_del|non_tensor_output_with_cpu_user", user
                        )
                        break

            if not new_cpu_nodes:
                break

            for new_cpu_node in new_cpu_nodes:
                self.acc_nodes.remove(new_cpu_node)

            self.reduce_acc_nodes_non_tensor_input_helper(new_cpu_nodes)