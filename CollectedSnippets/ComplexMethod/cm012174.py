def _find_schedulable_path(
        self, target: fx.Node, curr_overlap_node: fx.Node | None, why: WhyNoOverlap
    ) -> OrderedSet[fx.Node] | None:
        """Find path to target by collecting unscheduled dependencies."""
        # Get unscheduled ancestors
        unscheduled_ancestors = self.node_ancestors[target] - self.scheduled

        # only schedule non distributed, non compute nodes
        for node in unscheduled_ancestors:
            if is_compute_node(node):
                why("path blocked by compute node %s", node.name)
                return None

            if node in self.unscheduled_collectives:
                why("path blocked by unscheduled collective %s", node.name)
                return None

            # if we schedule a wait tensor whose start collective is hidden by the
            # current compute node we are scheduling, then we are effectively exposing it.
            # similarly, dont schedule a wait of a collective that could be otherwise hidden,
            # thus forcing it to be exposed.
            # however, if it is already hidden it's fine to schedule it
            if _schedulable_wait_node(node):
                info = self.collective_info[self.wait_to_start[node]]
                if (not info.is_exposed) and (
                    curr_overlap_node not in info.hiding_nodes
                ):
                    continue

                why(
                    "path blocked by wait node %s (exposed=%s, hidden_by_curr_overlap=%s)",
                    node.name,
                    info.is_exposed,
                    curr_overlap_node in info.hiding_nodes,
                )
                return None

            # Skip c10 ops and dtensor shard ops - they should be scheduled via main loop
            target_str = str(node.target)
            if "c10" in target_str or "_dtensor" in target_str:
                log.debug(
                    "Skipping c10/dtensor op %s in path to collective",
                    node.name,
                )
                return None

        return unscheduled_ancestors