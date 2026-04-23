def _try_reindex_pointwise_for_reduction(
        self,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
    ) -> bool:
        """
        Reindex a pointwise's iteration loops to match a reduction's
        groups. After reindexing, the shared reads have identical index
        expressions, enabling the codegen to CSE loads.

        Returns True if reindexing was applied.
        """
        from .codegen.simd import SIMDKernel

        if node1.is_reduction() and not node2.is_reduction():
            reduction_node, pw_node = node1, node2
        elif node2.is_reduction() and not node1.is_reduction():
            reduction_node, pw_node = node2, node1
        else:
            return False

        _, groups = reduction_node.group
        red_numel = typing.cast(sympy.Expr, groups[0])
        red_rnumel = typing.cast(sympy.Expr, groups[1])
        target_numel = red_numel * red_rnumel

        if not all(isinstance(sn, SchedulerNode) for sn in pw_node.get_nodes()):
            return False
        snodes = typing.cast(list[SchedulerNode], pw_node.get_nodes())

        # All snodes must have the same total iteration numel matching
        # the reduction's numel * rnumel so they can be reindexed identically.
        if not all(
            V.graph.sizevars.statically_known_equals(
                sympy_product(sn._sizes[0]), target_numel
            )
            for sn in snodes
        ):
            return False

        if not all(
            SIMDKernel.is_compatible((red_numel, red_rnumel), sn.get_ranges())
            for sn in snodes
        ):
            return False

        # Snapshot state before mutation so we can rollback if the
        # reindexed deps don't actually improve the fusion score.
        snapshots = [(sn, sn.snapshot_loop_state()) for sn in snodes]
        old_pw_group = (
            pw_node.group if isinstance(pw_node, FusedSchedulerNode) else None
        )

        for sn in snodes:
            sn.apply_loop_reindexing([red_numel, red_rnumel])

        if isinstance(pw_node, FusedSchedulerNode):
            pw_node.group = snodes[0].group
            refresh_group_node_dependencies(pw_node)

        # Verify reindexing actually increases shared deps.
        common_names = (
            node1.read_writes.buffer_names() & node2.read_writes.buffer_names()
        )
        n1_deps = {dep.name: dep for dep in node1.read_writes.reads_and_writes()}
        n2_deps = {dep.name: dep for dep in node2.read_writes.reads_and_writes()}
        has_benefit = any(
            self.deps_match_normalized(n1_deps[name], n2_deps[name])
            for name in common_names
        )
        if not has_benefit:
            for sn, state in snapshots:
                sn.restore_loop_state(state)
            if isinstance(pw_node, FusedSchedulerNode):
                assert old_pw_group is not None
                pw_node.group = old_pw_group
                refresh_group_node_dependencies(pw_node)
            return False

        # When loop ordering is disabled, re-extract deps with
        # normalize=True so variable names are canonical. This is
        # safe because no further loop reordering will occur.
        # Without this, reindexed deps use different var names
        # (e.g. c0 vs d0) causing exact dep comparisons to fail.
        if not config.loop_ordering_after_fusion:
            for sn in snodes:
                sn.refresh_dependencies(normalize=True, need_clear_tiling_cache=False)
            if isinstance(pw_node, FusedSchedulerNode):
                refresh_group_node_dependencies(pw_node)

        return True