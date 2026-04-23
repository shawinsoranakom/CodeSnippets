def _reorder_graph(self) -> None:
        """Reorder graph based on schedule."""
        exposed = [
            c
            for c in self.collective_info.values()
            if c.exposed_time_ms == c.estimated_time_ms
        ]

        potentially_hidden_collectives = self.compute_potential_hidden_collectives()
        bad_exposed = [
            c for c in exposed if c.start_node in potentially_hidden_collectives
        ]

        # Compute total exposed and potential exposed time
        total_exposed = sum(c.exposed_time_ms for c in self.collective_info.values())
        hideable_exposed_ms = sum(
            self.collective_info[c].exposed_time_ms
            for c in potentially_hidden_collectives
        )
        total_potential_exposed = sum(
            c.estimated_time_ms for c in self.collective_info.values()
        )

        counters["inductor"]["overlap_scheduling_exposed"] += len(exposed)
        counters["inductor"]["overlap_scheduling_bad_exposed"] += len(bad_exposed)
        counters["inductor"]["overlap_scheduling_potentially_hidden"] += len(
            potentially_hidden_collectives
        )
        counters["inductor"]["overlap_original_mem"] = self.original_peak_memory
        counters["inductor"]["rescheduled_mem"] = self.memory_tracker.peak_memory

        log.info(
            "Overlap scheduling results: exposed=%d, bad_exposed=%d, potentially_hidden=%d, "
            "original_peak_memory=%d bytes, rescheduled_peak_memory=%d bytes, "
            "total_exposed_ms=%.2f, hideable_exposed_ms=%.2f, total_potential_exposed_ms=%.2f, "
            "wasted_compute_ms=%.2f",
            len(exposed),
            len(bad_exposed),
            len(potentially_hidden_collectives),
            self.original_peak_memory,
            self.memory_tracker.peak_memory,
            total_exposed,
            hideable_exposed_ms,
            total_potential_exposed,
            self.wasted_compute,
        )

        self.reorder_graph()