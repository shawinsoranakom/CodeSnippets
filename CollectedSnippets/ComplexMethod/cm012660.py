def codegen_node(
        self, node: scheduler.FusedSchedulerNode | scheduler.SchedulerNode
    ):
        """
        Given a set of pre-fused nodes, generate a Triton kernel.
        """
        assert self.scheduler
        nodes = [
            node
            for node in node.get_nodes()
            if node.get_name() not in self.scheduler.removed_ops
        ]
        if len(nodes) == 0:
            return

        if torch._inductor.config.triton.coalesce_tiling_analysis:
            if len(nodes) != len(node.get_nodes()):
                assert self.scheduler
                node = scheduler.FusedSchedulerNode(self.scheduler, nodes)
            coalesce_analysis = analyze_memory_coalescing(node)
        else:
            coalesce_analysis = None

        return self._codegen_nodes(nodes, coalesce_analysis)