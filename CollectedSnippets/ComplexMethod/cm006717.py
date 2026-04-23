def get_properties_from_source_component(self):
        vertex = self.get_vertex()
        if vertex and hasattr(vertex, "incoming_edges") and vertex.incoming_edges:
            source_id = vertex.incoming_edges[0].source_id
            source_vertex = self.graph.get_vertex(source_id)
            component = source_vertex.custom_component
            source = component.display_name
            icon = component.icon
            possible_attributes = ["model_name", "model_id", "model"]
            for attribute in possible_attributes:
                if hasattr(component, attribute):
                    attr_value = getattr(component, attribute)
                    if attr_value:
                        model_name = _extract_model_name(attr_value)
                        if model_name:
                            return model_name, icon, source, component.get_id()
            return source, icon, component.display_name, component.get_id()
        return None, None, None, None