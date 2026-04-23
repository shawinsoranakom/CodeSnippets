def _handle_wait(self, node: fx.Node) -> None:
        """Handle scheduling a wait."""
        assert node in self.wait_to_start
        coll_start = self.wait_to_start[node]
        # For coalesced collectives, multiple waits share the same start node.
        # The first wait completes the collective; subsequent waits just schedule.
        if coll_start not in self.in_flight:
            self._schedule(node)
            return

        # Scheduling a wait of a collective also forces the wait
        # of every node enqueued prior to the collective on the
        # same process group
        group_name = get_group_name(coll_start)
        to_schedule: list[fx.Node] = []
        for in_flight_coll in self.in_flight:
            if in_flight_coll == coll_start:
                break
            if get_group_name(in_flight_coll) == group_name:
                to_schedule.append(in_flight_coll)

        for coll_to_schedule in to_schedule:
            self._handle_wait(self.collective_info[coll_to_schedule].wait_node)

        # If we are waiting on an exposed collective, use this time to
        # overlap on other PGs.
        info = self.collective_info[coll_start]
        if info.exposed_time_ms > 0:
            exposed_time = info.exposed_time_ms
            exclude_pg = group_name

            remaining_time_per_pg = self._reduce_exposed_time_of_in_flight_collectives(
                node, exposed_time, exclude_pg=exclude_pg
            )
            self._schedule_collectives_for_overlap(
                node, remaining_time_per_pg, exclude_pg=exclude_pg
            )

        self.in_flight_bytes -= self.in_flight[coll_start].size_bytes
        del self.in_flight[coll_start]
        self._schedule(node)