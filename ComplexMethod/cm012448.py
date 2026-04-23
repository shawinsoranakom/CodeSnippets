def _get_outer_loop_fusion_depth(self, node1, node2):
        DISABLE_OUTER_LOOP_FUSION = 0
        if not all(
            type(node)
            in (OuterLoopFusedSchedulerNode, FusedSchedulerNode, SchedulerNode)
            for node in (node1, node2)
        ):
            return DISABLE_OUTER_LOOP_FUSION

        _node1 = (
            node1.get_outer_nodes()[-1]
            if isinstance(node1, OuterLoopFusedSchedulerNode)
            else node1
        )
        assert isinstance(_node1, (FusedSchedulerNode, SchedulerNode))
        _node2 = (
            node2.get_outer_nodes()[0]
            if isinstance(node2, OuterLoopFusedSchedulerNode)
            else node2
        )
        assert isinstance(_node2, (FusedSchedulerNode, SchedulerNode))

        _, (vars1, reduce1) = _node1.group
        _, (vars2, reduce2) = _node2.group
        if vars1 == () and vars2 == () and reduce1 != () and reduce2 != ():
            # Reduction only
            return DISABLE_OUTER_LOOP_FUSION
        if all(type(node) is OuterLoopFusedSchedulerNode for node in (node1, node2)):
            return (
                node1.outer_loop_fusion_depth
                if node1.outer_loop_fusion_depth == node2.outer_loop_fusion_depth
                else DISABLE_OUTER_LOOP_FUSION
            )
        outer_loop_fusion_depth = min(len(vars1), len(vars2))
        if (
            outer_loop_fusion_depth >= 1
            and vars1[:outer_loop_fusion_depth] == vars2[:outer_loop_fusion_depth]
        ):
            if any(
                type(node) is OuterLoopFusedSchedulerNode for node in (node1, node2)
            ):
                _compare_node = (
                    node1 if type(node1) is OuterLoopFusedSchedulerNode else node2
                )
                if _compare_node.outer_loop_fusion_depth == outer_loop_fusion_depth:
                    # Same outer loop fusion depth as prev nodes in OuterLoopFusedSchedulerNode
                    return outer_loop_fusion_depth
                else:
                    return DISABLE_OUTER_LOOP_FUSION
            else:
                # First 2 nodes to generate OuterLoopFusedSchedulerNode
                return outer_loop_fusion_depth
        return DISABLE_OUTER_LOOP_FUSION