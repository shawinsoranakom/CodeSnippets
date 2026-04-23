def _preserves_hiding_intervals(
        self,
        bucket_info: CollBucket,
        candidate: fx.Node,
        start_pos: fx.Node,
        wait_pos: fx.Node,
        why: WhyNoBucket,
    ) -> bool:
        """
        Check that (start_pos, wait_pos) doesn't violate any hiding intervals or collectives.

        Collects all execution and hiding intervals in the affected timeline regions,
        then checks:
        1. All bucket hiding compute stays between new start/wait
        2. No other collective's compute interval is enclosed by bucket execution interval
        3. No other collective's execution interval encloses bucket compute intervals
        """
        # Collect all collectives being bucketed
        all_bucketed_colls = [candidate] + list(bucket_info.collectives)
        all_bucketed_waits = [
            self.collective_info[coll].wait_node for coll in all_bucketed_colls
        ]

        # Collect hiding compute positions for the bucket
        bucket_hiding_compute_positions = []
        for coll in all_bucketed_colls:
            for coll_hiding_node in self.collective_info[coll].hiding_nodes:
                bucket_hiding_compute_positions.append(
                    self.node_to_event[coll_hiding_node].position
                )

        # Get new positions
        new_start_event = self.node_to_event[start_pos]
        new_wait_event = self.node_to_event[wait_pos]

        # Check 1: All bucket hiding compute must be between new start and wait
        for compute_pos in bucket_hiding_compute_positions:
            if not (new_start_event.position < compute_pos < new_wait_event.position):
                why(
                    "hiding compute at pos %d not between start %d and wait %d",
                    compute_pos,
                    new_start_event.position,
                    new_wait_event.position,
                )
                return False

        def get_wait(n: fx.Node) -> fx.Node:
            return self.collective_info[n].wait_node

        def get_pos(n: fx.Node) -> int:
            return self.node_to_event[n].position

        latest_start_pos = max(get_pos(candidate), get_pos(bucket_info.collectives[0]))
        earliest_wait_pos = min(
            get_pos(get_wait(candidate)), get_pos(get_wait(bucket_info.collectives[0]))
        )

        # Bucket execution interval
        bucket_execution_interval = (new_start_event.position, new_wait_event.position)

        # Because collectives on the same PG operate under LIFO semantics,
        # it's only possible for us to force an early realization of an unrelated collective
        # by delaying a start or raising a wait.
        # We search in the interval from old_start -> new_start, to see if would be
        # forcing another collective to be realized prior to its hiding nodes.
        # Similarly, we search from old_wait -> new_wait, in the reverse direction,
        # to check the same thing.

        execution_intervals = [bucket_execution_interval]
        hiding_intervals = [
            (bucket_execution_interval[0], pos)
            for pos in bucket_hiding_compute_positions
        ]

        curr_event = new_start_event.next
        while curr_event is not None and curr_event.position < latest_start_pos:
            if (
                curr_event.node not in all_bucketed_colls
                and curr_event.node not in all_bucketed_waits
            ):
                exec_interval, hiding_interval_list = self._get_intervals(curr_event)
                if exec_interval:
                    execution_intervals.append(exec_interval)
                hiding_intervals.extend(hiding_interval_list)
            curr_event = curr_event.next

        curr_event = new_wait_event.prev
        while curr_event is not None and curr_event.position > earliest_wait_pos:
            if (
                curr_event.node not in all_bucketed_colls
                and curr_event.node not in all_bucketed_waits
            ):
                exec_interval, hiding_interval_list = self._get_intervals(curr_event)
                if exec_interval:
                    execution_intervals.append(exec_interval)
                hiding_intervals.extend(hiding_interval_list)
            curr_event = curr_event.prev

        # Check: no hiding interval should be enclosed by any execution interval
        def enclosed_interval(inner: tuple[int, int], outer: tuple[int, int]) -> bool:
            return outer[0] < inner[0] and inner[1] < outer[1]

        for hiding_interval in hiding_intervals:
            for execution_interval in execution_intervals:
                if enclosed_interval(hiding_interval, execution_interval):
                    why(
                        "hiding interval %s enclosed by execution interval %s",
                        hiding_interval,
                        execution_interval,
                    )
                    return False

        return True