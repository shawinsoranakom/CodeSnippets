def mark_branch(self, vertex_id: str, state: str, output_name: str | None = None) -> None:
        visited = self._mark_branch(vertex_id=vertex_id, state=state, output_name=output_name)
        new_predecessor_map, _ = self.build_adjacency_maps(self.edges)
        new_predecessor_map = {k: v for k, v in new_predecessor_map.items() if k in visited}
        if vertex_id in self.cycle_vertices:
            # Remove dependencies that are not in the cycle and have run at least once
            new_predecessor_map = {
                k: [dep for dep in v if dep in self.cycle_vertices and dep in self.run_manager.ran_at_least_once]
                for k, v in new_predecessor_map.items()
            }
        self.run_manager.update_run_state(
            run_predecessors=new_predecessor_map,
            vertices_to_run=self.vertices_to_run,
        )