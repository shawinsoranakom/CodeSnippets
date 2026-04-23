def _get_next_nodes(self) -> list[fx.Node]:
        """
        Get next node(s) to schedule.

        When max_off_bucket_bytes is set, off-path collectives of the same type
        (same bucket_key) are batched together to enable bucketing them in
        overlap_preserving_bucketer. Bucket size is limited by max_off_bucket_bytes.
        """
        if self.off_path_ready:
            _, node = self.off_path_ready[0]

            should_schedule = False
            if not self.on_path_ready or node in self.scheduled:
                should_schedule = True
            elif _schedulable_wait_node(node):
                # Defer exposed waits until hidden or over memory budget
                info = self.collective_info[self.wait_to_start[node]]
                over_budget = (
                    self.memory_tracker.current_memory_bytes
                    > self.allowed_peak_memory_bytes
                )
                should_schedule = not info.is_exposed or over_budget
            elif self.max_off_bucket_bytes is not None and node in self.collective_info:
                # Batch off-path collectives: schedule when bucket threshold is reached
                bucket_key = get_full_bucket_key(node, self.bucket_mode)
                bucket_size = self.off_path_ready_potential_buckets[bucket_key]
                should_schedule = bucket_size >= self.max_off_bucket_bytes
            elif self.dominates_reduce_scatter(node):
                # Only schedule off-path nodes that dominate reduce_scatters after original position
                should_schedule = self.node_idx[node] <= self.last_on_path_node_idx

            if should_schedule:
                heapq.heappop(self.off_path_ready)

                # If batching enabled and this is a collective, gather same-type collectives
                if (
                    self.max_off_bucket_bytes is not None
                    and node in self.collective_info
                ):
                    node_key = get_full_bucket_key(node, self.bucket_mode)
                    if node_key is not None:
                        same_type_nodes = [node]
                        total_bytes = self.collective_info[node].size_bytes
                        indices_to_remove = []

                        # Scan the off_path_ready queue for same-key collectives
                        for i, (_, candidate) in enumerate(self.off_path_ready):
                            if candidate in self.scheduled:
                                continue
                            if candidate not in self.collective_info:
                                continue
                            candidate_key = get_full_bucket_key(
                                candidate, self.bucket_mode
                            )
                            if candidate_key == node_key:
                                candidate_bytes = self.collective_info[
                                    candidate
                                ].size_bytes
                                # Check bucket size limit before adding
                                if (
                                    total_bytes + candidate_bytes
                                    > self.max_off_bucket_bytes
                                ):
                                    continue  # Skip but keep looking for smaller ones
                                same_type_nodes.append(candidate)
                                total_bytes += candidate_bytes
                                indices_to_remove.append(i)

                        # Remove collected nodes from heap (reverse order to preserve indices)
                        for i in reversed(indices_to_remove):
                            self.off_path_ready.pop(i)
                        if indices_to_remove:
                            heapq.heapify(self.off_path_ready)

                        return same_type_nodes

                return [node]

        return [heapq.heappop(self.on_path_ready)[1]]