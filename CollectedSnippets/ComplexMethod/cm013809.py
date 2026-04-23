def _set_activations(self) -> None:
        """Flood the graph to identify activations."""

        required = {Category.INPUT, Category.ACTIVATION}
        also_allowed = {Category.PARAMETER, Category.TEMPORARY}
        for node in self._data_flow_graph.flow_nodes:
            inputs = {(key, value) for key, (_, value) in node.inputs.items()}
            input_categories = {self._categories.get(*i) for i in inputs}

            if (
                (input_categories & required)
                and not (input_categories - (required | also_allowed))
                #
                # Stop filling when we reach the backward pass.
                and RecordScope.BACKWARD_FUNCTION not in get_scopes(node._event)
            ):
                for i in node.outputs.items():
                    self._categories.setdefault_by_version(*i, Category.ACTIVATION)