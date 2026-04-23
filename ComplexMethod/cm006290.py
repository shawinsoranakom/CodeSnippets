def _resolve_root_output(
        self,
        flow_outputs: dict[str, Any] | None,
        error: Exception | None,
        extracted_metadata: FlowMetadata,
    ) -> str:
        """Determine the root output from flow outputs, error, or component extraction."""
        root_output = extracted_metadata["chat_output"]
        if not error and flow_outputs:
            # Look for Chat Output component's message in flow_outputs
            chat_output_found = False
            for key, value in flow_outputs.items():
                if any(name in key for name in CHAT_OUTPUT_NAMES) and isinstance(value, dict) and "message" in value:
                    chat_output_msg = self._convert_to_openlayer_type(value["message"])
                    if chat_output_msg:
                        root_output = chat_output_msg
                        chat_output_found = True
                        break

            # If no Chat Output found, try Agent component output
            if not chat_output_found:
                for key, value in flow_outputs.items():
                    if any(name in key for name in AGENT_NAMES) and isinstance(value, dict):
                        response = value.get("response")
                        if response:
                            root_output = self._convert_to_openlayer_type(response)
                            chat_output_found = True
                            break

            # If still not found, try common output keys at top level
            if not chat_output_found:
                converted_outputs = self._convert_to_openlayer_types(flow_outputs)
                for key_name in ("message", "response", "result", "output"):
                    if key_name in converted_outputs:
                        root_output = converted_outputs[key_name]
                        break

        return root_output