def shared_data_after_reordering_loop(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> int:
        """
        Right now just greedily reorder the loop of node1 to be compatible with node2,
        but ideally we should have some heuristics to reorder the loop for node2
        to be compatible with node1 if that's more efficient.

        Return the amount of shared data re-computed in this method.
        If no such recomputation happens, return -1 (not return 0 since 0 is a valid
        amount of shared data).

        """

        # TODO Don't do loop reordering/reindexing for CPU for now.
        # Should debug more why it does not work for CPU codegen
        if any(n.is_cpu() for n in [node1, node2]):
            return -1

        # in some rare case, a template can be passed in.
        # Check test_interaction_with_multi_template in test_loop_ordering.py
        # and https://github.com/pytorch/pytorch/issues/165579
        if node1.is_template() or node2.is_template():
            return -1

        common_buffer_names = (
            node1.read_writes.buffer_names() & node2.read_writes.buffer_names()
        )
        if not common_buffer_names:
            return -1

        if config.loop_ordering_after_fusion:
            score = self._try_reorder_loops_for_candidates(node1, node2)
            if score >= 0:
                return score

        # No reordering candidates found (or loop ordering disabled).
        # Try reindexing the pointwise to match the reduction's iteration
        # domain (e.g., [1024, 8192] -> [65536, 128] for RMS norm with
        # reshape), then retry loop reordering if enabled. The retry is
        # needed because FusedSchedulerNodes may have more loop vars than
        # the reindexed pointwise (e.g., 3 vs 2), and only the normalize()
        # comparison in _try_reorder_loops_for_candidates handles that
        # num_vars mismatch.
        if (
            not config.loop_reindexing_after_fusion
            or not self._try_reindex_pointwise_for_reduction(node1, node2)
        ):
            return -1

        if config.loop_ordering_after_fusion:
            score = self._try_reorder_loops_for_candidates(node1, node2)
            if score >= 0:
                return score

        return self.score_fusion_memory(node1, node2)