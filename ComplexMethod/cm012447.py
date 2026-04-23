def _can_fuse_nodes_with_compatible_ranges(self, node1, node2):
        # Here we try to fuse SchedulerNode/FusedSchedulerNode with compatible ranges
        # e.g. (s0, s1, s2) and (s0 * s1 * s2)
        _, (vars1, reduce1) = node1.group
        _, (vars2, reduce2) = node2.group

        c1 = reduce1 == () and reduce2 == ()
        c2 = math.prod(vars1) == math.prod(vars2)
        c3 = len(vars1) == 1 or len(vars2) == 1
        if not (c1 and c2 and c3):
            return False

        node_to_recomp = node1 if len(vars1) < len(vars2) else node2
        ref_node = node2 if len(vars1) < len(vars2) else node1

        # We can not recompute sizes and body for nodes other than SchedulerNode
        # TODO: we can extend fusion support with compatible ranges for FusedSchedulerNode
        if isinstance(node_to_recomp, FusedSchedulerNode):
            return False

        # It may happen that node1 and node2 compatible number of elements
        # but different original ranges, for example:
        # {d0: s0, d1: s1, d2: s2} vs {d0: s0*s1*s2}
        # See https://github.com/pytorch/pytorch/pull/120077/files#r1500427848 for more details
        # TODO: we can fix if it allows us to CSE at least one of the variables

        assert isinstance(node_to_recomp, SchedulerNode)
        if isinstance(node_to_recomp.node, ir.TemplateBuffer):
            return False
        assert isinstance(node_to_recomp.node, ir.ComputedBuffer)
        # node.data.get_size() is a cheaper version of node.get_read_writes().var_ranges
        # but without variable name
        ranges2 = node_to_recomp.node.data.get_size()
        ranges1 = None
        if isinstance(ref_node, FusedSchedulerNode):
            ranges_set = OrderedSet[tuple[Any, ...]]()
            for snode in ref_node.snodes:
                assert isinstance(snode, SchedulerNode)
                if isinstance(snode.node, ir.TemplateBuffer):
                    break
                assert isinstance(snode.node, ir.ComputedBuffer)
                ranges_set.add(tuple(snode.node.data.get_size()))

            if len(ranges_set) != 1:
                return False

            ranges1 = list(next(iter(ranges_set)))
        else:
            assert isinstance(ref_node, SchedulerNode)
            assert isinstance(ref_node.node, ir.ComputedBuffer)
            ranges1 = ref_node.node.data.get_size()  # type: ignore[assignment]

        if ranges1 != ranges2:
            return False

        snapshots = self._snapshot_node_loop_states(node_to_recomp)
        snapshots.extend(self._snapshot_node_loop_states(ref_node))
        try:
            return self._align_compatible_range_nodes(node1, node2)
        finally:
            for node, state in reversed(snapshots):
                node.restore_loop_state(state)