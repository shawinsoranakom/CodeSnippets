def prepare(self, stop_component_id: str | None = None, start_component_id: str | None = None):
        self.initialize()
        if stop_component_id and start_component_id:
            msg = "You can only provide one of stop_component_id or start_component_id"
            raise ValueError(msg)

        if stop_component_id or start_component_id:
            try:
                first_layer = self.sort_vertices(stop_component_id, start_component_id)
            except Exception:  # noqa: BLE001
                logger.exception("Error sorting vertices")
                first_layer = self.sort_vertices()
        else:
            first_layer = self.sort_vertices()

        for vertex_id in first_layer:
            self.run_manager.add_to_vertices_being_run(vertex_id)
            if vertex_id in self.cycle_vertices:
                self.run_manager.add_to_cycle_vertices(vertex_id)
        self._first_layer = sorted(first_layer)
        self._run_queue = deque(self._first_layer)
        self._prepared = True
        self._record_snapshot()
        return self