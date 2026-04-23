def create_combo_kernel_nodes(self, num_ck_nodes: int | None = None) -> None:
        """
        Groups parallel nodes
        """
        fused_nodes = OrderedSet(self.nodes)
        count = 0
        num_nodes_orig = len(self.nodes)
        log.debug("ComboKernels: Generating with num_ck_nodes = %s...", num_ck_nodes)
        for num, node_list in enumerate(
            ForeachKernelSchedulerNode.group_nodes_for_combo_kernels(self)
        ):
            node_list = ForeachKernelSchedulerNode.combinable_nodes(node_list)
            if len(node_list) < 2:
                continue
            if num_ck_nodes is not None and count > num_ck_nodes:
                break
            if not self.speedup_by_combo_kernel(node_list):
                log.debug("ComboKernels: Not speeding up %d-th group", num)
                continue
            count += 1
            enable_autotune = config.combo_kernels_autotune > 0
            group_snode = ForeachKernelSchedulerNode(
                node_list[0].scheduler,
                node_list,
                use_custom_partition_algo=True,
                enable_autotune=enable_autotune,
            )
            log.info(
                "ComboKernels: Combining %d nodes for %d-th group",
                len(node_list),
                num,
            )
            for node in node_list:
                fused_nodes.remove(node)
            fused_nodes.add(group_snode)
            self.name_to_fused_node.update(
                {n.get_name(): group_snode for n in group_snode.get_nodes()}
            )
            # Propagate stream assignment so codegen can place the combo
            # kernel in the correct stream context.
            stream = self.node_to_stream.get(node_list[0])
            if stream is not None:
                self.node_to_stream[group_snode] = stream
        self.nodes = sorted(fused_nodes, key=lambda x: x.min_order)
        self.nodes = self.topological_sort_schedule(self.nodes)
        log.info(
            "Generated ComboKernel nodes: %d ComboKernels, totally %d -> %d nodes",
            count,
            num_nodes_orig,
            len(self.nodes),
        )
        self.prune_redundant_deps(self.nodes)