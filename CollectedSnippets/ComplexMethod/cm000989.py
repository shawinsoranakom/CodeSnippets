def _build_inputs_message(
        self,
        graph: GraphModel,
        suffix: str,
    ) -> str:
        """Build a message describing available inputs for an agent."""
        inputs_list = get_inputs_from_schema(graph.input_schema)
        required_names = [i["name"] for i in inputs_list if i["required"]]
        optional_names = [i["name"] for i in inputs_list if not i["required"]]

        message_parts = [f"Agent '{graph.name}' accepts the following inputs:"]
        if required_names:
            message_parts.append(f"Required: {', '.join(required_names)}.")
        if optional_names:
            message_parts.append(
                f"Optional (have defaults): {', '.join(optional_names)}."
            )
        if not inputs_list:
            message_parts = [f"Agent '{graph.name}' has no required inputs."]
        message_parts.append(suffix)

        return " ".join(message_parts)