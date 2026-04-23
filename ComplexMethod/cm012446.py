def fuse(self, node1, node2):
        if node1.is_foreach() or node2.is_foreach():
            return ForeachKernelSchedulerNode.fuse(node1, node2)
        elif node1.is_template():
            assert not node2.is_template()
            return FusedSchedulerNode.fuse(node1, node2)
        else:
            if (
                self._why_fuse_nodes(node1, node2)
                == ReasonFusedNodes.COMPATIBLE_RANGES_NO_REDUCTION
            ):
                assert self._align_compatible_range_nodes(node1, node2), (
                    node1.group,
                    node2.group,
                )
                return FusedSchedulerNode.fuse(node1, node2)
            elif self.can_fuse_vertical_outer_loop(node1, node2):
                return OuterLoopFusedSchedulerNode.fuse(
                    node1, node2, self._get_outer_loop_fusion_depth(node1, node2)
                )
            else:
                return FusedSchedulerNode.fuse(node1, node2)