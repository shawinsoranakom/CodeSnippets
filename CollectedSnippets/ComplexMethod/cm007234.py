def _exclude_branch_conditionally(
        self, vertex_id: str, visited: set, excluded: set, output_name: str | None = None, *, skip_first: bool = False
    ) -> None:
        """Recursively excludes vertices in a branch for conditional routing."""
        if vertex_id in visited:
            return
        visited.add(vertex_id)

        # Don't exclude the first vertex (the router itself)
        if not skip_first:
            self.conditionally_excluded_vertices.add(vertex_id)
            excluded.add(vertex_id)

        for child_id in self.parent_child_map[vertex_id]:
            # If we're at the router (skip_first=True) and have an output_name,
            # only follow edges from that specific output
            if skip_first and output_name:
                edge = self.get_edge(vertex_id, child_id)
                if edge and edge.source_handle.name != output_name:
                    continue
            # After the first level, exclude all descendants
            self._exclude_branch_conditionally(child_id, visited, excluded, output_name=None, skip_first=False)