def __call__(self) -> dict[torch.fx.Node, NodeSet]:
        result: dict[torch.fx.Node, NodeSet] = {}
        acc_nodes = list(self.acc_nodes)

        for node in acc_nodes:
            if node in result:
                continue
            if node.op not in CALLABLE_NODE_OPS:
                continue
            if "tensor_meta" in node.meta:
                continue
            if node not in self.acc_nodes:
                continue

            fusion_group: FxNetAccFusionsFinder.FusionGroup = self.FusionGroup(
                top_node_idx=self.node_index[node],
                nodes={node},
                inputs=set(node.all_input_nodes),
                nodes_need_process={node},
            )
            while fusion_group.nodes_need_process:
                node = fusion_group.nodes_need_process.pop()
                self.recursive_add_node(
                    fusion_group,
                    fusion_group.inputs,
                    visited=set(),
                )

                # Optionally add downstream nodes
                if "tensor_meta" not in node.meta:
                    for user in node.users:
                        if user.op not in CALLABLE_NODE_OPS:
                            continue
                        if user in fusion_group.nodes:
                            continue

                        fusion_group.add_node(user)
                        self.recursive_add_node(
                            fusion_group,
                            fusion_group.inputs,
                            visited=set(),
                        )

                # Add some upstream nodes
                for arg in node.all_input_nodes:
                    if arg.op not in CALLABLE_NODE_OPS:
                        continue
                    if "tensor_meta" in arg.meta:
                        continue
                    if arg in fusion_group.nodes:
                        continue

                    fusion_group.add_node(arg)
                    fusion_group.top_node_idx = min(
                        fusion_group.top_node_idx, self.node_index[arg]
                    )
                    self.recursive_add_node(
                        fusion_group,
                        fusion_group.inputs,
                        visited=set(),
                    )

            if not (set(fusion_group.nodes) <= self.acc_nodes):
                self.acc_nodes -= fusion_group.nodes
            else:
                for n in fusion_group.nodes:
                    result[n] = fusion_group.nodes

        return result