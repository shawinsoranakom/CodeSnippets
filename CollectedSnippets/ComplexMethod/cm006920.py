def _find_matching_output_method(self, input_name: str, value: Component):
        """Find the output method from the given component and input name.

        Find the output method from the given component (`value`) that matches the specified input (`input_name`)
        in the current component.
        This method searches through all outputs of the provided component to find outputs whose types match
        the input types of the specified input in the current component. If exactly one matching output is found,
        it returns the corresponding method. If multiple matching outputs are found, it raises an error indicating
        ambiguity. If no matching outputs are found, it raises an error indicating that no suitable output was found.

        Args:
            input_name (str): The name of the input in the current component to match.
            value (Component): The component whose outputs are to be considered.

        Returns:
            Callable: The method corresponding to the matching output.

        Raises:
            ValueError: If multiple matching outputs are found, if no matching outputs are found,
                        or if the output method is invalid.
        """
        # Retrieve all outputs from the given component
        outputs = value._outputs_map.values()
        # Prepare to collect matching output-input pairs
        matching_pairs = []
        # Get the input object from the current component
        input_ = self._inputs[input_name]
        # Iterate over outputs to find matches based on types
        matching_pairs = [
            (output, input_)
            for output in outputs
            for output_type in output.types
            # Check if the output type matches the input's accepted types
            if input_.input_types and output_type in input_.input_types
        ]
        # If multiple matches are found, raise an error indicating ambiguity
        if len(matching_pairs) > 1:
            matching_pairs_str = self._build_error_string_from_matching_pairs(matching_pairs)
            msg = self.build_component_error_message(
                f"There are multiple outputs from {value.display_name} that can connect to inputs: {matching_pairs_str}"
            )
            raise ValueError(msg)
        # If no matches are found, raise an error indicating no suitable output
        if not matching_pairs:
            msg = self.build_input_error_message(input_name, f"No matching output from {value.display_name} found")
            raise ValueError(msg)
        # Get the matching output and input pair
        output, input_ = matching_pairs[0]
        # Ensure that the output method is a valid method name (string)
        if not isinstance(output.method, str):
            msg = self.build_component_error_message(
                f"Method {output.method} is not a valid output of {value.display_name}"
            )
            raise TypeError(msg)
        return getattr(value, output.method)