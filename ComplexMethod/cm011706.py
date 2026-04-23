def sub_node_can_fuse(
        self,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
        other_nodes: tuple[BaseSchedulerNode, ...],
    ):
        """
        node1 is from the current mix order reduction; node2 is another node we want to fuse in.

        other_nodes are passed in to check if fusion will introduce producer/consumer relationship
        between the inner and outer reduction. If yes, we don't fuse.
        """
        assert not isinstance(node1, FusedMixOrderReductions)
        assert not isinstance(node2, FusedMixOrderReductions)

        # When we fuse extra nodes into a FusedMixOrderReductions node,
        # we should not allow recursive mix-order reduction being
        # created.
        if not self.scheduler.can_fuse(node1, node2, allow_mix_order_reduction=False):
            return False

        # Since node1 is from the current mix order reduction, if node1 is
        # contiguous, the fused node should also be contiguous.
        if MixOrderReduction.is_contiguous_node(
            node1
        ) and not MixOrderReduction.is_contiguous_node(node2):
            return False

        def _get_ancestors(nodes: tuple[BaseSchedulerNode, ...]) -> OrderedSet[str]:
            out = OrderedSet()
            return out.union(*(n.ancestors for n in nodes))

        def _get_operation_names(
            nodes: tuple[BaseSchedulerNode, ...],
        ) -> OrderedSet[str]:
            out = OrderedSet()
            return out.union(*(n.get_operation_names() for n in nodes))

        if other_nodes:
            if (_get_ancestors((node1, node2)) & _get_operation_names(other_nodes)) or (
                _get_ancestors(other_nodes) & _get_operation_names((node1, node2))
            ):
                return False

        return (
            not node2.is_reduction()
            or self.scheduler.score_fusion_memory(node1, node2, count_bytes=False)
            >= self.numel
        )