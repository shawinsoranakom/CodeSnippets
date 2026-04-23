def process_tool_response(self, tool_response: str, **_kwargs) -> str:
        logger.info("Calling process_tool_response of PostToolProcessor")
        tool_response_str = self._get_tool_response_str(tool_response)

        # First check if this looks like an error message with bullet points (SPARC rejection)
        if "❌" in tool_response_str or "•" in tool_response_str:
            logger.info("Detected error message with special characters, skipping JSON parsing")
            return tool_response_str

        try:
            # Only attempt to parse content that looks like JSON
            if (tool_response_str.startswith("{") and tool_response_str.endswith("}")) or (
                tool_response_str.startswith("[") and tool_response_str.endswith("]")
            ):
                tool_response_json = ast.literal_eval(tool_response_str)
                if not isinstance(tool_response_json, (list, dict)):
                    tool_response_json = None
            else:
                tool_response_json = None
        except (json.JSONDecodeError, TypeError, SyntaxError, ValueError) as e:
            logger.info(
                f"An error in converting the tool response to json, this will skip the code generation component: {e}"
            )
            tool_response_json = None

        if tool_response_json is not None and len(str(tool_response_json)) > self.response_processing_size_threshold:
            llm_client_obj = self._get_altk_llm_object(use_output_val=False)
            if llm_client_obj is not None:
                config = CodeGenerationComponentConfig(llm_client=llm_client_obj, use_docker_sandbox=False)

                middleware = CodeGenerationComponent(config=config)
                input_data = CodeGenerationRunInput(
                    messages=[],
                    nl_query=self.user_query,
                    tool_response=tool_response_json,
                )
                output = None
                try:
                    output = middleware.process(input_data, AgentPhase.RUNTIME)
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Exception in executing CodeGenerationComponent: {e}")
                if output is not None and hasattr(output, "result"):
                    logger.info(f"Output of CodeGenerationComponent: {output.result}")
                    return output.result
        return tool_response