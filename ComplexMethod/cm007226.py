def add_component(self, component: Component, component_id: str | None = None) -> str:
        component_id = component_id or component.get_id()
        if component_id in self.vertex_map:
            return component_id
        component.set_id(component_id)
        if component_id in self.vertex_map:
            msg = f"Component ID {component_id} already exists"
            raise ValueError(msg)
        frontend_node = component.to_frontend_node()
        self._vertices.append(frontend_node)
        vertex = self._create_vertex(frontend_node)
        vertex.add_component_instance(component)
        self._add_vertex(vertex)
        if component.get_edges():
            for edge in component.get_edges():
                self._add_edge(edge)

        if component.get_components():
            for _component in component.get_components():
                self.add_component(_component)

        return component_id