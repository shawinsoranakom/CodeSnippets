def _try_timeline_position(
        self,
        bucket_info: CollBucket,
        candidate: fx.Node,
        start_pos: fx.Node,
        wait_pos: fx.Node,
        why: WhyNoBucket,
    ) -> bool:
        """
        Try a specific timeline position for the candidate.
        Returns True if valid and merges are successful.
        """
        candidate_info = self.collective_info[candidate]
        candidate_wait = candidate_info.wait_node

        # Quick check: does this violate hiding intervals?
        if not self._preserves_hiding_intervals(
            bucket_info, candidate, start_pos, wait_pos, why
        ):
            return False

        # Determine which start needs to move
        existing_coll = bucket_info.collectives[0]
        if start_pos == existing_coll:
            start_to_move = candidate
        else:
            assert start_pos == candidate
            start_to_move = existing_coll

        # Remove start from timeline
        start_prev, start_next = self.remove_from_event(start_to_move)

        # Check if starts can be merged
        if self.aug_graph.has_path(existing_coll, candidate) or self.aug_graph.has_path(
            candidate, existing_coll
        ):
            # Restore start constraints
            self.restore_to_event(start_to_move, start_prev, start_next)
            why("path exists between starts")
            return False

        # Merge starts
        self.aug_graph.merge_to_set(existing_coll, candidate)

        # Determine which wait needs to move
        existing_wait = self.collective_info[existing_coll].wait_node
        candidate_wait = self.collective_info[candidate].wait_node

        if wait_pos == existing_wait:
            wait_to_move = candidate_wait
        else:
            wait_to_move = existing_wait

        # Remove wait from timeline
        wait_prev, wait_next = self.remove_from_event(wait_to_move)

        # Check if waits can be merged
        if self.aug_graph.has_path(
            existing_wait, candidate_wait
        ) or self.aug_graph.has_path(candidate_wait, existing_wait):
            # Restore wait constraints
            self.restore_to_event(wait_to_move, wait_prev, wait_next)
            # Unmerge the start we just merged
            self.aug_graph.unmerge_node(candidate)
            # Restore start constraints
            self.restore_to_event(start_to_move, start_prev, start_next)
            why("path exists between waits")
            return False

        # Merge waits - success!
        self.aug_graph.merge_to_set(existing_wait, candidate_wait)

        # Update node_to_event for moved nodes
        target_start_event = self.node_to_event[start_pos]
        target_wait_event = self.node_to_event[wait_pos]

        self.node_to_event[candidate] = target_start_event
        self.node_to_event[candidate_wait] = target_wait_event
        self.node_to_event[existing_coll] = target_start_event
        self.node_to_event[existing_wait] = target_wait_event

        return True