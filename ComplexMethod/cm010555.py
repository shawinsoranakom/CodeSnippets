def _populate_cpu_children(self):
        """Populate child events into each underlying FunctionEvent object.

        One event is a child of another if [s1, e1) is inside [s2, e2). Where
        s1 and e1 would be start and end of the child event's interval. And
        s2 and e2 start and end of the parent event's interval

        Example: In event list [[0, 10], [1, 3], [3, 4]] would have make [0, 10]
        be a parent of two other intervals.

        If for any reason two intervals intersect only partially, this function
        will not record a parent child relationship between then.
        """
        # Some events can be async (i.e. start and end on different threads),
        # since it's generally undefined how to attribute children ranges to
        # async ranges, we do not use them when calculating nested ranges and stats
        sync_events = [
            evt
            for evt in self
            if not evt.is_async and evt.device_type == DeviceType.CPU
        ]
        events = sorted(
            sync_events,
            key=attrgetter("thread"),
        )
        # Group by both thread and node_id, so that events that happen to have
        # the same thread_id but are from different nodes aren't incorrectly
        # grouped together.
        threads = itertools.groupby(
            events, key=lambda event: (event.thread, event.node_id)
        )

        # For each thread we keep a stack of current nested parents.
        # We maintain the invariant that each interval is a subset of all other
        # intervals lower in the stack.
        #
        # First we sort the intervals by their start time. Then we iterate over them.
        # Every time we see a new interval we remove several parents from
        # the top until we restore the invariant. Then parent child relationship
        # if recorded if the stack is not empty.
        # Finally we add new interval to the list
        #
        # Algorithm has O(N * log(N)) complexity where N is number of
        # intervals
        for _thread_id, thread_events in threads:
            thread_events_ = sorted(
                thread_events,
                key=lambda event: [event.time_range.start, -event.time_range.end],
            )
            current_events: list[FunctionEvent] = []
            for event in thread_events_:
                while len(current_events) > 0:
                    parent = current_events[-1]
                    if (
                        event.time_range.start >= parent.time_range.end
                        or event.time_range.end > parent.time_range.end
                    ):
                        # this can't be a parent
                        current_events.pop()
                    else:
                        parent.append_cpu_child(event)
                        if event.cpu_parent is not None:
                            raise AssertionError(
                                f"There is already a CPU parent event for {event.key}"
                            )
                        event.set_cpu_parent(parent)
                        break

                current_events.append(event)