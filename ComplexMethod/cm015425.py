def _reorder_communication_preserving_peak_memory(
            snodes: list[BaseSchedulerNode],
        ) -> list[BaseSchedulerNode]:
            if torch._inductor.config.runtime_estimations_mms_benchmark:
                cache = get_estimate_runtime_cache()
                for snode in snodes:
                    if _get_mm_like_fn(snode) is None:
                        continue
                    cache_key = get_estimate_runtime_cache_key_from_snode(snode)
                    if cache.lookup(cache_key) is None:
                        raise AssertionError(
                            f"Expected cache.lookup({cache_key}) to not be None"
                        )

            if torch._inductor.config_comms.runtime_estimations_align_across_all_distributed_ranks:
                for snode in snodes:
                    if snode.override_estimated_runtime is None:
                        raise AssertionError(
                            "Expected snode.override_estimated_runtime to not be None"
                        )
            nonlocal node_stats
            (
                reordered_snodes,
                node_stats,
            ) = _reorder_communication_preserving_peak_memory_internal(snodes)
            return reordered_snodes