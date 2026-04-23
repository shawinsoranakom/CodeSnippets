def can_fuse(
        scheduler: Scheduler,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
        shared_data_score: int,
    ) -> bool:
        """
        Heuristics to prevent fusion applied to both horizontal and vertical fusions.  Heuristics here should not
        be needed for correctness and tweaking them may yield additional performance.

        See also some related heuristics that can be changed via config:
            - config.triton.tiling_prevents_pointwise_fusion
            - config.triton.tiling_prevents_reduction_fusion
            - config.aggressive_fusion (will cause this function to be called more times)
        """
        if shared_data_score == 0 and (
            not config.aggressive_fusion or node1.is_reduction() or node2.is_reduction()
        ):
            if is_metric_table_enabled("fusion_failure_due_to_indexing_mismatch"):
                common_buf_names: OrderedSet[str] = (
                    node1.read_writes.buffer_names() & node2.read_writes.buffer_names()
                )
                if len(common_buf_names) > 0:
                    get_metric_table("fusion_failure_due_to_indexing_mismatch").add_row(
                        # pyrefly: ignore [bad-argument-type]
                        lambda: {
                            "pre_grad_graph_id": V.graph.graph_id,
                            "post_grad_graph_id": V.graph.post_grad_graph_id,
                            "node1_name": node1.get_name(),
                            "node2_name": node2.get_name(),
                            "node1_debug_str": write_text(node1.debug_str()),
                            "node2_debug_str": write_text(node2.debug_str()),
                            "common_buffer_names": list(common_buf_names),  # type: ignore[dict-item]
                            "failure_reason": scheduler.decide_fusion_fail_reason(
                                node1, node2, common_buf_names
                            ),
                        }
                    )

                    WhyNoFuse(node1, node2)("no shared data due to indexing mismatch")
                    return False
            WhyNoFuse(node1, node2)("no shared data")
            return False  # heuristic not needed for correctness

        if (
            not node1.is_foreach()
            and not node2.is_foreach()
            and len(node1.get_nodes()) + len(node2.get_nodes()) > config.max_fusion_size
        ):
            WhyNoFuse(node1, node2)("exceeds max fusion")
            return False  # heuristic not needed for correctness

        if scheduler.can_fusion_increase_peak_memory(node1, node2):
            WhyNoFuse(node1, node2)("Fusion will increase peak memory")
            return False

        if (
            config.max_fusion_unique_io_buffers is not None
            and scheduler.fusion_prevent_too_many_reads_and_writes(
                node1,
                node2,
                config.max_fusion_unique_io_buffers,
            )
        ):
            WhyNoFuse(node1, node2)("fusion_prevent_too_many_reads_and_writes")
            return False

        return True