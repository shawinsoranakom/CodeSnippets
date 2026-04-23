def _schedule_collectives_for_overlap(
        self,
        overlap_node: fx.Node,
        remaining_time_per_pg: dict[str, float],
        exclude_pg: str | None = None,
    ) -> None:
        """Opportunistically schedule collectives that can be hidden by available overlap time."""
        if not remaining_time_per_pg or all(
            t <= 0 for t in remaining_time_per_pg.values()
        ):
            return

        overlap_node_ancestors = self.node_ancestors[overlap_node]

        # Compile candidates - limit by distance to bound compile time
        candidates = []
        for i, collective in enumerate(self.unscheduled_collectives):
            if i > self.max_node_distance:
                break

            pg_name = get_group_name(collective)
            if pg_name == exclude_pg:
                continue

            if (
                not self.off_compute_path(collective)
                and self.compute_index_domination[collective]
                - self.current_compute_index
                > self.max_compute_pre_fetch
            ):
                continue

            candidates.append(collective)

        def get_priority(n: fx.Node) -> int:
            dominates_next_compute = (
                self.compute_index_domination[n] == self.current_compute_index + 1
            )
            if dominates_next_compute:
                return 0  # Dominates next compute layer - most urgent
            elif self.off_compute_path(n) and self.dominates_reduce_scatter(n):
                return 1  # Off-path but blocks reduce_scatter
            elif not self.off_compute_path(n):
                return 2  # On-path but not immediate
            else:
                return 3  # Off-path, doesn't block reduce_scatter

        candidates.sort(
            key=lambda n: (
                get_priority(n),
                self.compute_index_domination[n],
                self.node_idx[n],
            ),
        )

        if self.prioritize_bucketing_during_scheduling:
            # group candidates by bucket key first so same-bucket
            # collectives are scheduled together, maximizing bucketing opportunities
            bucket_groups: dict[object, list[fx.Node]] = defaultdict(list)
            for coll in candidates:
                key = get_full_bucket_key(coll, self.bucket_mode)
                bucket_groups[key].append(coll)

            # Sort bucket groups by minimum domination index, larger groups first as tiebreaker
            sorted_bucket_keys = sorted(
                bucket_groups.keys(),
                key=lambda k: (
                    min(self.compute_index_domination[c] for c in bucket_groups[k]),
                    -len(bucket_groups[k]),
                ),
            )

            # Flatten back to ordered candidate list
            candidates = []
            for b_key in sorted_bucket_keys:
                group = bucket_groups[b_key]
                group.sort(
                    key=lambda n: (self.compute_index_domination[n], self.node_idx[n])
                )
                candidates.extend(group)

        for collective in candidates:
            pg_name = get_group_name(collective)
            pg_available_time = remaining_time_per_pg[pg_name]

            if pg_available_time <= 0:
                continue

            why = WhyNoOverlap(overlap_node, collective)
            info = self.collective_info[collective]

            if (
                collective in overlap_node_ancestors
                or overlap_node in self.node_ancestors[collective]
            ):
                why("dependency conflict")
                continue

            # Check if prefetching would exceed memory budget
            if self._prefetch_would_exceed_memory_budget(collective):
                why("prefetch would exceed memory budget")
                continue

            # Try to free memory by forcing hidden waits
            while (
                self.in_flight
                and (self.max_in_flight_bytes - self.in_flight_bytes) < info.size_bytes
                and self._wait_is_hidden(self._get_oldest_wait(), overlap_node)
            ):
                self._force_oldest_wait()

            if (self.max_in_flight_bytes - self.in_flight_bytes) < info.size_bytes:
                why("in-flight memory limit")
                continue

            # Check if we can reach this collective without scheduling compute, other collectives, or waits
            path = self._find_schedulable_path(collective, overlap_node, why)
            if path is None:
                continue

            log.debug(
                "Overlapping collective %s with node %s: coll_domination=%d, current_depth=%d",
                collective.name,
                overlap_node.name,
                self.compute_index_domination[collective],
                self.current_compute_index,
            )

            # TODO: We previously tracked path compute time and added it back to available
            # overlap time. With per-PG tracking this is complex: if there were in-flight
            # collectives on one PG but not another, we can't add path time back to the PG
            # that wasn't in-flight

            # Schedule path and collective
            self._schedule_path_to_collective(path, overlap_node)
            self._handle_collective_start(collective)
            self._update_cumulative_prefetch_memory(collective, info)

            # Update exposed time for this collective
            overlap_amount = min(pg_available_time, info.exposed_time_ms)
            info.exposed_time_ms -= overlap_amount
            info.hiding_nodes.add(overlap_node)

            # Update available time for this PG
            remaining_time_per_pg[pg_name] -= overlap_amount

            if sum(remaining_time_per_pg.values()) == 0:
                break

        if remaining_time_per_pg:
            self.wasted_compute += min(remaining_time_per_pg.values())