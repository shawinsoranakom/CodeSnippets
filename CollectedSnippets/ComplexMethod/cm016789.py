async def stage_node_execution(self):
        assert self.staged_node_id is None
        if self.is_empty():
            return None, None, None
        available = self.get_ready_nodes()
        while len(available) == 0 and self.externalBlocks > 0:
            # Wait for an external block to be released
            await self.unblockedEvent.wait()
            self.unblockedEvent.clear()
            available = self.get_ready_nodes()
        if len(available) == 0:
            cycled_nodes = self.get_nodes_in_cycle()
            # Because cycles composed entirely of static nodes are caught during initial validation,
            # we will 'blame' the first node in the cycle that is not a static node.
            blamed_node = cycled_nodes[0]
            for node_id in cycled_nodes:
                display_node_id = self.dynprompt.get_display_node_id(node_id)
                if display_node_id != node_id:
                    blamed_node = display_node_id
                    break
            ex = DependencyCycleError("Dependency cycle detected")
            error_details = {
                "node_id": blamed_node,
                "exception_message": str(ex),
                "exception_type": "graph.DependencyCycleError",
                "traceback": [],
                "current_inputs": []
            }
            return None, error_details, ex

        self.staged_node_id = self.ux_friendly_pick_node(available)
        return self.staged_node_id, None, None