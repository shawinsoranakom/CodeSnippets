def _validate_edge(self, source, target) -> None:
        # Validate that the outputs of the source node are valid inputs
        # for the target node
        # .outputs is a list of Output objects as dictionaries
        # meaning: check for "types" key in each dictionary
        self.source_types = [output for output in source.outputs if output["name"] == self.source_handle.name]

        # Check if this is an loop input (loop target handle with output_types)
        is_loop_input = hasattr(self.target_handle, "input_types") and self.target_handle.input_types
        loop_input_types = []

        if is_loop_input:
            # For loop inputs, use the configured input_types
            # (which already includes original type + loop_types from frontend)
            loop_input_types = list(self.target_handle.input_types)
            # Backward compatibility: old flows may have Data/DataFrame types
            self.valid = any(types_compatible(output["types"], loop_input_types) for output in self.source_types)
            # Find the first matching type (considering migrations)
            self.matched_type = next(
                (
                    output_type
                    for output in self.source_types
                    for output_type in output["types"]
                    if types_compatible([output_type], loop_input_types)
                ),
                None,
            )
        else:
            # Standard validation for regular inputs
            self.target_reqs = target.required_inputs + target.optional_inputs
            # Both lists contain strings and sometimes a string contains the value we are
            # looking for e.g. comgin_out=["Chain"] and target_reqs=["LLMChain"]
            # so we need to check if any of the strings in source_types is in target_reqs
            # Backward compatibility: old flows may have Data/DataFrame types
            self.valid = any(types_compatible(output["types"], self.target_reqs) for output in self.source_types)
            # Update the matched type to be the first found match (considering migrations)
            self.matched_type = next(
                (
                    output_type
                    for output in self.source_types
                    for output_type in output["types"]
                    if types_compatible([output_type], self.target_reqs)
                ),
                None,
            )

        no_matched_type = self.matched_type is None
        if no_matched_type:
            logger.debug(self.source_types)
            logger.debug(self.target_reqs if not is_loop_input else loop_input_types)
            msg = f"Edge between {source.vertex_type} and {target.vertex_type} has no matched type."
            raise ValueError(msg)