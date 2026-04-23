def _set_inputs(self, input_components: list[str], inputs: dict[str, str], input_type: InputType | None) -> None:
        """Updates input vertices' parameters with the provided inputs, filtering by component list and input type.

        Only vertices whose IDs or display names match the specified input components and whose IDs contain
        the input type (unless input type is 'any' or None) are updated. Raises a ValueError if a specified
        vertex is not found.
        """
        for vertex_id in self._is_input_vertices:
            vertex = self.get_vertex(vertex_id)
            # If the vertex is not in the input_components list
            if input_components and (vertex_id not in input_components and vertex.display_name not in input_components):
                continue
            # If the input_type is not any and the input_type is not in the vertex id
            # Example: input_type = "chat" and vertex.id = "OpenAI-19ddn"
            if input_type is not None and input_type != "any" and input_type not in vertex.id.lower():
                continue
            if vertex is None:
                msg = f"Vertex {vertex_id} not found"
                raise ValueError(msg)
            vertex.update_raw_params(inputs, overwrite=True)