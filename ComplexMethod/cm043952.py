def get_options_for_dimension(
        self, dimension_id: str | None = None
    ) -> list[dict[str, str]]:
        """Get the available options for a given dimension, based on the current selections.

        Parameters
        ----------
        dimension_id : str
            The ID of the dimension to get options for.

        Returns
        -------
        list[dict]
            A list of available options, where each option is a dictionary with
            'label' and 'value' keys.
        """
        dimension_id = dimension_id or self.get_next_dimension_to_select()
        if not dimension_id:
            return []
        if dimension_id not in self._dimensions:
            raise ValueError(
                f"Dimension '{dimension_id}' not found for dataflow '{self.dataflow_id}'."
            )

        key_parts: list = []
        for dim in self._dimensions:
            if self._selections[dim] is not None:
                key_parts.append(self._selections[dim])
            else:
                # Use wildcard '*' for unselected dimensions instead of empty string
                # Empty string creates malformed URLs like '../'
                key_parts.append("*")
        key = ".".join(key_parts)

        constraints = self._builder.metadata.get_available_constraints(
            dataflow_id=self.dataflow_id,
            key=key,
            component_id=dimension_id,
        )
        # Store the last constraints response for time period validation
        self._last_constraints_response = constraints

        options: list[dict[str, str]] = []
        key_values = constraints.get("key_values", [])
        for kv in key_values:
            if kv.get("id") == dimension_id:
                codelist_map = self._get_codelist_for_dim(dimension_id)
                for value_id in kv.get("values", []):
                    options.append(
                        {
                            "label": codelist_map.get(value_id, value_id),
                            "value": value_id,
                        }
                    )
        return options