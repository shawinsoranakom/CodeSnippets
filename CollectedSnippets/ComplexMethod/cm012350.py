def _find_buckets(
        self,
        collective_group: OrderedSet[fx.Node],
        internode_pgs: OrderedSet[str],
    ) -> list[CollBucket]:
        """Find valid buckets within a group of similar collectives."""
        max_bucket_bytes = int(self.max_bucket_memory_gb * 1024 * 1024 * 1024)
        buckets = []
        processed: OrderedSet[fx.Node] = OrderedSet()
        if len(collective_group) == 0:
            return []

        current_pg = get_group_name(next(iter(collective_group)))

        bucket_exposed_first = self._should_bucket_exposed_first(
            collective_group, current_pg, internode_pgs
        )
        if bucket_exposed_first:
            # Sort by overlap ratio (ascending) to bucket least hidden collectives first.
            # Exposed collectives benefit most from bucketing since their latency is on the
            # critical path. Prioritizing them also preserves hiding relationships for
            # already-hidden collectives, which have less to gain from bucketing.
            sorted_collectives = sorted(
                collective_group,
                key=lambda n: (self._compute_overlap_ratio(n), self.node_idx[n]),
            )
        else:
            sorted_collectives = sorted(
                collective_group,
                key=lambda n: self.node_idx[n],
            )

        for i, start_node in enumerate(sorted_collectives):
            if start_node in processed:
                continue

            if (
                start_node in self.all_hiding_nodes
                or self.collective_info[start_node].wait_node in self.all_hiding_nodes
            ):
                continue

            # Initialize bucket with first collective
            bucket_info = CollBucket(
                collectives=[start_node],
                total_bytes=self.collective_info[start_node].size_bytes,
            )
            processed.add(start_node)

            # Greedy optimization: stop after consecutive failures
            consecutive_failures = 0
            max_consecutive_failures = 20
            start_node_idx = self.node_idx[start_node]

            # Check candidates in sorted order, break when beyond max distance
            for candidate in sorted_collectives[i + 1 : i + 1 + self.max_coll_distance]:
                candidate_bytes = self.collective_info[candidate].size_bytes
                # proxy on memory use, if we see a too large bucket,
                # dont look for another, later bucket
                if bucket_info.total_bytes + candidate_bytes > max_bucket_bytes:
                    break

                if candidate in processed:
                    continue

                candidate_node_idx = self.node_idx[candidate]
                if (
                    bucket_exposed_first
                    and abs(candidate_node_idx - start_node_idx)
                    > max_consecutive_failures
                ):
                    # Since collectives are sorted by overlap ratio rather than graph
                    # position, skip candidates too far apart in the graph to avoid
                    # creating buckets that block future bucketing opportunities.
                    continue

                if self._can_add_to_bucket(bucket_info, candidate):
                    bucket_info.collectives.append(candidate)
                    bucket_info.total_bytes += candidate_bytes
                    processed.add(candidate)
                    consecutive_failures = 0  # Reset on success
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        break

            if len(bucket_info.collectives) > 1:
                buckets.append(bucket_info)

        return buckets