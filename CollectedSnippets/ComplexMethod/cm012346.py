def build_timeline(self, pg: str) -> PGEvent | None:
        """
        Build a timeline of important events (starts, waits, hiding compute) for this process group
        and constrain this ordering in the augmented graph.

        Sequential dependencies are added between all events because NCCL collectives on the same
        process group execute on the same CUDA stream, enforcing LIFO semantics where later-issued
        collectives must complete before earlier ones can finish.
        """

        head = None
        prev_event = None
        position = 0
        hiding_nodes = OrderedSet()

        for node in self.scheduled:
            node_type = None

            # Determine if this node is relevant for this PG
            if node in self.collective_info and get_group_name(node) == pg:
                node_type = "starts"
                hiding_nodes |= self.collective_info[node].hiding_nodes
            elif _schedulable_wait_node(node):
                wait_coll = _get_collective_node_from_wait(node)
                if isinstance(wait_coll, fx.Node) and get_group_name(wait_coll) == pg:
                    node_type = "waits"
                # Wait for a different PG but hiding a collective on this PG
                elif node in hiding_nodes:
                    node_type = "compute"
            elif is_compute_node(node) or node in hiding_nodes:
                node_type = "compute"

            if node_type is None:
                continue

            event = PGEvent(node=node, event_type=node_type, position=position)  # type: ignore[arg-type]

            event.insert_between(prev_event, None)

            # Add sequential dependency to augmented graph
            if prev_event:
                self.aug_graph.add_extra_dep(n=event.node, dep=prev_event.node)
            else:
                head = event

            prev_event = event
            position += 1

        return head