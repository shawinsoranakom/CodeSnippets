def _align_compatible_range_nodes(self, node1, node2):
        assert isinstance(node1, (SchedulerNode, FusedSchedulerNode))
        assert isinstance(node2, (SchedulerNode, FusedSchedulerNode))

        _, (vars1, reduce1) = node1.group
        _, (vars2, reduce2) = node2.group
        assert reduce1 == () and reduce2 == (), (reduce1, reduce2)

        node_to_recomp = node1 if len(vars1) < len(vars2) else node2
        ref_node = node2 if len(vars1) < len(vars2) else node1
        assert isinstance(node_to_recomp, SchedulerNode)

        ref_indexing_constraints = self._get_indexing_ranges_exprs(ref_node)
        node_to_recomp.recompute_size_and_body(
            extra_indexing_constraints=ref_indexing_constraints
        )

        _, (vars1, _) = node1.group
        _, (vars2, _) = node2.group
        if vars1 == vars2:
            return True

        node_to_recomp_indexing_constraints = self._get_indexing_ranges_exprs(
            node_to_recomp
        )
        if isinstance(ref_node, SchedulerNode):
            ref_node.recompute_size_and_body(
                extra_indexing_constraints=node_to_recomp_indexing_constraints
            )
        else:
            assert isinstance(ref_node, FusedSchedulerNode)
            for snode in ref_node.snodes:
                assert isinstance(snode, SchedulerNode)
                snode.recompute_size_and_body(
                    extra_indexing_constraints=node_to_recomp_indexing_constraints
                )

        _, (vars1, _) = node1.group
        _, (vars2, _) = node2.group
        return vars1 == vars2