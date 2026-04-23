async def _get_result(self, requester: Vertex, target_handle_name: str | None = None) -> Any:
        """Retrieves the result of the built component.

        If the component has not been built yet, a ValueError is raised.

        Returns:
            The built result if use_result is True, else the built object.
        """
        if not self.built:
            default_value: Any = UNDEFINED
            for edge in self.get_edge_with_target(requester.id):
                # We need to check if the edge is a normal edge
                if edge.is_cycle and edge.target_param:
                    if edge.target_param in requester.output_names:
                        default_value = None
                    else:
                        default_value = requester.get_value_from_template_dict(edge.target_param)

            if default_value is not UNDEFINED:
                return default_value
            msg = f"Component {self.display_name} has not been built yet"
            raise ValueError(msg)

        if requester is None:
            msg = "Requester Vertex is None"
            raise ValueError(msg)

        edges = self.get_edge_with_target(requester.id)
        result = UNDEFINED
        for edge in edges:
            if (
                edge is not None
                and edge.source_handle.name in self.results
                and edge.target_handle.field_name == target_handle_name
            ):
                # Get the result from the output instead of the results dict
                try:
                    output = self.get_output(edge.source_handle.name)

                    if output.value is UNDEFINED:
                        result = self.results[edge.source_handle.name]
                    else:
                        result = cast("Any", output.value)
                except NoComponentInstanceError:
                    result = self.results[edge.source_handle.name]
                break
        if result is UNDEFINED:
            if edge is None:
                msg = f"Edge not found between {self.display_name} and {requester.display_name}"
                raise ValueError(msg)
            if edge.source_handle.name not in self.results:
                msg = f"Result not found for {edge.source_handle.name}. Results: {self.results}"
                raise ValueError(msg)
            msg = f"Result not found for {edge.source_handle.name} in {edge}"
            raise ValueError(msg)
        return result