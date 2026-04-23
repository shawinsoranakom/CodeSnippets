def run(self) -> torch.fx.GraphModule:
        """Run the scheduling algorithm."""
        # All ranks must make identical decisions on overlap reordering,
        # Thus we must have identical runtime estimations across ranks.
        # For now we do benchmarking only for compute nodes.
        self._align_compute_nodes_runtime_estimations_across_all_distributed_ranks()

        while self.on_path_ready or self.off_path_ready:
            if self._should_force_wait_for_memory():
                self._force_oldest_wait()
                continue

            nodes = self._get_next_nodes()

            for node in nodes:
                # we don't always remove nodes from the heap when we schedule them
                if node in self.scheduled:
                    continue

                if node.op == "placeholder":
                    self._schedule(node)
                elif node in self.collective_info:
                    self._handle_collective_start(node)
                elif _schedulable_wait_node(node):
                    self._handle_wait(node)
                else:
                    self._handle_compute_or_other(node)

                # Track progress for off-path scheduling - only for nodes from main queue
                if not self.off_compute_path(node):
                    self.last_on_path_node_idx = max(
                        self.last_on_path_node_idx, self.node_idx[node]
                    )
                else:
                    # Decrement off-path bucket bytes when scheduling
                    if node in self.collective_info:
                        bucket_key = get_full_bucket_key(node, self.bucket_mode)
                        node_bytes = self.collective_info[node].size_bytes
                        self.off_path_ready_potential_buckets[bucket_key] -= node_bytes

        self._reorder_graph()

        # Finalize: bucket collectives (if enabled), inline fusions, apply deps
        from torch._inductor.fx_passes.overlap_preserving_bucketer import (
            finalize_overlap_scheduling,
        )

        finalize_overlap_scheduling(
            gm=self.gm,
            collective_info=self.collective_info,
            scheduled=self.scheduled,
            collective_bucketing=self.collective_bucketing,
            insert_overlap_deps=self.insert_overlap_deps,
            max_bucket_memory_gb=2.0,
            max_coll_distance=self.max_node_distance,
            region_of=self.region_of,
            bucket_exposed_first=self.bucket_exposed_first,
            bucket_only_internode_comms=self.bucket_only_internode_comms,
            bucket_mode=self.bucket_mode,
        )

        if self.log_final_collectives_estimations:
            from torch._inductor.fx_passes.node_runtime_estimation import (
                _log_graph_collective_benchmarks,
            )

            _log_graph_collective_benchmarks(
                self.gm, "fx_collectives_estimations_after_overlap_bucketing"
            )

        return self.gm