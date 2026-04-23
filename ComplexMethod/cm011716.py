def create_foreach_nodes(self) -> None:
        removed_node_names: OrderedSet[str] = OrderedSet()
        fe_nodes = []
        kept_node_names = self.name_to_fused_node.keys()

        for names in V.graph.lists.values():
            names = [
                name
                for name in names
                if name in kept_node_names
                and not isinstance(self.name_to_node[name], NopKernelSchedulerNode)
            ]
            if not names:
                # All nodes eliminated
                continue

            removed_node_names.update(names)
            snodes = [self.name_to_node[name] for name in names]

            enable_autotune = config.combo_kernels_autotune > 1
            fe_node = ForeachKernelSchedulerNode(
                self,
                snodes,
                use_custom_partition_algo=False,
                enable_autotune=enable_autotune,
            )

            fe_nodes.append(fe_node)

            for name in names:
                self.name_to_fused_node[name] = fe_node

        self.nodes = [
            node for node in self.nodes if node.get_name() not in removed_node_names
        ] + list(fe_nodes)