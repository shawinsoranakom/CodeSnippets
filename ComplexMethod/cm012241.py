def _bucket_group(self, coll_nodes: list[fx.Node]) -> None:
        assert len(coll_nodes) > 0, "bucketed coll_nodes should have nonzero node"

        waits = [self.collective_info[n].wait_node for n in coll_nodes]
        # Use earliest wait insertion point
        first_wait = min(waits, key=lambda w: self.node_idx[w])
        # Find insertion location
        first = coll_nodes[0]
        next_node = first
        while next_node in coll_nodes:
            next_node = next_node.next

        if is_all_gather(first):
            new_nodes, replacements = merge_all_gather_bucket(
                self.graph,
                coll_nodes,
                wait_insertion_point=first_wait,
                insert_before=next_node,
                mode=self.bucket_mode,
            )
        elif is_reduce_scatter(first):
            new_nodes, replacements = merge_reduce_scatter_bucket(
                self.graph,
                coll_nodes,
                wait_insertion_point=first_wait,
                insert_before=next_node,
                mode=self.bucket_mode,
            )
        else:
            raise ValueError(
                "bucket non all_gather/reduce_scatter node is not supported"
            )

        logger.debug(f"bucketing nodes: {coll_nodes} into {new_nodes}")  # noqa: G004

        # Identify the new wait(s) and their collective start in a single pass
        wait_to_start = {
            n: start
            for n in new_nodes
            if (start := _get_collective_node_from_wait(n)) is not None
        }
        assert len(wait_to_start) >= 1, (
            f"Expected at least one new wait, got none in {new_nodes}"
        )
        new_waits = list(wait_to_start)
        new_start: fx.Node = wait_to_start[new_waits[0]]
        # Use last wait as the canonical wait for scheduling (same node when len == 1)
        new_wait = new_waits[-1]

        # Track bucketed node types on this bucketer instance so it doesn't leak
        # when the same graph is processed by multiple ManualOverlapScheduler
        # invocations (e.g. separate forward and backward passes).
        node_type = (
            "bucketed_all_gather" if is_all_gather(first) else "bucketed_reduce_scatter"
        )
        wait_set = OrderedSet(new_waits)
        for n in new_nodes:
            if n in wait_set:
                self.bucketed_node_types[n] = node_type + "_wait"
                self.node_to_wait_map[n] = new_wait
            elif n is new_start:
                self.bucketed_node_types[n] = node_type