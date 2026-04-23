def generate_node_schedule(self, nodes, numel, rnumel):
        node_schedule: list[Any] = []
        done = OrderedSet[scheduler.BaseSchedulerNode]()
        # Writes with a reduced shape, meaning they are only present once the
        # reduction loop has ended
        not_ready_yet_nodes: OrderedSet[str] = OrderedSet()
        current_loop_buffer_usage: OrderedSet[str] = OrderedSet()
        maybe_split_index: int | None = None

        def fits_in_main_body(n):
            _, (node_numel, node_rnumel) = n.group
            return (node_numel == numel and node_rnumel == rnumel) or (
                node_numel == numel * rnumel and node_rnumel == 1
            )

        def fits_outside_reduction(n):
            _, (node_numel, node_rnumel) = n.group
            return node_numel == numel and node_rnumel == 1 and rnumel != 1

        def expect_improved_memory_usage(n):
            for read in n.read_writes.reads:
                if read.name in current_loop_buffer_usage:
                    return True
            return False

        def schedule_node_in_loop(n):
            done.add(n)
            node_schedule.append(n)
            current_loop_buffer_usage.update([x.name for x in n.read_writes.reads])

            # A scan is modelled as a reduction in the scheduler but has a
            # full sized output that can be used inside the loop body
            if (
                n.is_reduction()
                and isinstance(n, scheduler.SchedulerNode)
                and isinstance(n.node, ir.ComputedBuffer)
                and not isinstance(n.node.data, ir.Scan)
            ):
                not_ready_yet_nodes.add(n.get_name())
            else:  # this node is available within the loop
                current_loop_buffer_usage.update([x.name for x in n.read_writes.writes])

        @contextlib.contextmanager
        def end_current_reduction_loop():
            nonlocal maybe_split_index
            if node_schedule and node_schedule[-1] is EnableReduction:
                node_schedule.pop()
            else:
                node_schedule.append(DisableReduction)
            if maybe_split_index:
                node_schedule.insert(maybe_split_index, DisableReduction)
                node_schedule.insert(maybe_split_index + 1, EnableReduction)
                maybe_split_index = None
            yield
            node_schedule.append(EnableReduction)
            not_ready_yet_nodes.clear()
            current_loop_buffer_usage.clear()

        def requires_closing_previous_reduction(node, node_schedule):
            if rnumel == 1:
                return False
            if not not_ready_yet_nodes & node.ancestors:
                return False
            assert node_schedule and not isinstance(
                node_schedule[-1], (EnableReduction, DisableReduction)
            )
            return bool(not_ready_yet_nodes)

        for node in nodes:
            if node in done:
                continue
            done.add(node)

            if fits_in_main_body(node):
                if requires_closing_previous_reduction(node, node_schedule):
                    with end_current_reduction_loop():
                        pass  # need to start a new reduction loop

                if current_loop_buffer_usage and not expect_improved_memory_usage(node):
                    # If we don't improve memory usage, then it is better to split into two loops
                    maybe_split_index = maybe_split_index or len(node_schedule)
                else:
                    # Memory usage got improved, cancel the loop split
                    maybe_split_index = None

                schedule_node_in_loop(node)
            elif fits_outside_reduction(node):
                with end_current_reduction_loop():
                    node_schedule.append(node)
            else:
                raise NotImplementedError(
                    f"unexpected group: ({numel}, {rnumel}) != {node.group[1]}"
                )

        return node_schedule