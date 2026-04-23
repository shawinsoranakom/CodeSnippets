def _extract_flow_metadata(
        self,
        components: Iterable[Any],
        error: Exception | None = None,
    ) -> FlowMetadata:
        metadata: FlowMetadata = {
            "chat_output": "Flow completed",
            "chat_input": {},
            "start_time": None,
            "end_time": None,
            "error": None,
        }

        # Handle error case - set output to error message
        if error:
            metadata["error"] = str(error)
            metadata["chat_output"] = f"Error: {error}"

        for step in components:
            # Extract Chat Output (only if no error, since error takes precedence)
            if step.name in CHAT_OUTPUT_NAMES and not error:
                chat_output = self._safe_get_input(step, "input_value")
                if chat_output:
                    metadata["chat_output"] = chat_output

            # Extract Agent response as fallback (when no Chat Output component)
            if (
                step.name in AGENT_NAMES
                and not error
                and metadata["chat_output"] == "Flow completed"
                and hasattr(step, "output")
                and isinstance(step.output, dict)
            ):
                response = step.output.get("response")
                if response:
                    metadata["chat_output"] = response if isinstance(response, str) else str(response)

            # Extract Chat Input
            if step.name in CHAT_INPUT_NAMES:
                input_val = self._safe_get_input(step, "input_value")
                if input_val:
                    metadata["chat_input"] = {"flow_input": input_val}

            # Extract timing
            if (
                hasattr(step, "start_time")
                and step.start_time
                and (metadata["start_time"] is None or step.start_time < metadata["start_time"])
            ):
                metadata["start_time"] = step.start_time
            if (
                hasattr(step, "end_time")
                and step.end_time
                and (metadata["end_time"] is None or step.end_time > metadata["end_time"])
            ):
                metadata["end_time"] = step.end_time

        return metadata