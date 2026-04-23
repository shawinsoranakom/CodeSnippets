def fuse(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> FusedSchedulerNode:
        """
        Fuse two nodes
        """
        if node1.is_foreach() or node2.is_foreach():
            return ForeachKernelSchedulerNode.fuse(node1, node2)
        elif MixOrderReduction.are_mix_order_reductions(node1, node2):
            return FusedMixOrderReductions(node1, node2)
        elif isinstance(node1, FusedMixOrderReductions):
            return node1.fuse_with(node2)
        elif isinstance(node1, ExternKernelSchedulerNode) and isinstance(
            node2, SchedulerNode
        ):
            assert isinstance(node1.node, ir.UserDefinedTritonKernel)
            return FusedExternTritonKernelSchedulerNode.epilogue_fuse(node1, node2)
        else:
            return FusedSchedulerNode.fuse(node1, node2)