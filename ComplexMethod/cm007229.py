def activate_state_vertices(self, name: str, caller: str) -> None:
        """Activates vertices associated with a given state name.

        Marks vertices with the specified state name, as well as their successors and related
        predecessors. The state manager is then updated with the new state record.
        """
        vertices_ids = set()
        new_predecessor_map = {}
        activated_vertices = []
        for vertex_id in self.is_state_vertices:
            caller_vertex = self.get_vertex(caller)
            vertex = self.get_vertex(vertex_id)
            if vertex_id == caller or vertex.display_name == caller_vertex.display_name:
                continue
            ctx_key = vertex.raw_params.get("context_key")
            if isinstance(ctx_key, str) and name in ctx_key and vertex_id != caller and isinstance(vertex, StateVertex):
                activated_vertices.append(vertex_id)
                vertices_ids.add(vertex_id)
                successors = self.get_all_successors(vertex, flat=True)
                # Update run_manager.run_predecessors because we are activating vertices
                # The run_prdecessors is the predecessor map of the vertices
                # we remove the vertex_id from the predecessor map whenever we run a vertex
                # So we need to get all edges of the vertex and successors
                # and run self.build_adjacency_maps(edges) to get the new predecessor map
                # that is not complete but we can use to update the run_predecessors
                successors_predecessors = set()
                for sucessor in successors:
                    successors_predecessors.update(self.get_all_predecessors(sucessor))

                edges_set = set()
                for _vertex in [vertex, *successors, *successors_predecessors]:
                    edges_set.update(_vertex.edges)
                    if _vertex.state == VertexStates.INACTIVE:
                        _vertex.set_state("ACTIVE")

                    vertices_ids.add(_vertex.id)
                edges = list(edges_set)
                predecessor_map, _ = self.build_adjacency_maps(edges)
                new_predecessor_map.update(predecessor_map)

        vertices_ids.update(new_predecessor_map.keys())
        vertices_ids.update(v_id for value_list in new_predecessor_map.values() for v_id in value_list)

        self.activated_vertices = activated_vertices
        self.vertices_to_run.update(vertices_ids)
        self.run_manager.update_run_state(
            run_predecessors=new_predecessor_map,
            vertices_to_run=self.vertices_to_run,
        )