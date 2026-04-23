async def _attempt_llm_call_with_validation(
        self,
        credentials: llm.APIKeyCredentials,
        input_data: Input,
        current_prompt: list[dict[str, Any]],
        tool_functions: list[dict[str, Any]],
    ) -> Any:
        """
        Attempt a single LLM call with tool validation.

        Returns the response if successful, raises ValueError if validation fails.
        """
        resp = await llm.llm_call(
            compress_prompt_to_fit=input_data.conversation_compaction,
            credentials=credentials,
            llm_model=input_data.model,
            prompt=current_prompt,
            max_tokens=input_data.max_tokens,
            tools=tool_functions,
            ollama_host=input_data.ollama_host,
            parallel_tool_calls=input_data.multiple_tool_calls,
        )

        # Track LLM usage stats per call
        self.merge_stats(
            NodeExecutionStats(
                input_token_count=resp.prompt_tokens,
                output_token_count=resp.completion_tokens,
                cache_read_token_count=resp.cache_read_tokens,
                cache_creation_token_count=resp.cache_creation_tokens,
                llm_call_count=1,
                provider_cost=resp.provider_cost,
            )
        )

        if not resp.tool_calls:
            return resp
        validation_errors_list: list[str] = []
        for tool_call in resp.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except Exception as e:
                validation_errors_list.append(
                    f"Tool call '{tool_name}' has invalid JSON arguments: {e}"
                )
                continue

            # Find the tool definition to get the expected arguments
            tool_def = next(
                (
                    tool
                    for tool in tool_functions
                    if tool["function"]["name"] == tool_name
                ),
                None,
            )
            if tool_def is None:
                if len(tool_functions) == 1:
                    tool_def = tool_functions[0]
                else:
                    validation_errors_list.append(
                        f"Tool call for '{tool_name}' does not match any known "
                        "tool definition."
                    )

            # Get parameters schema from tool definition
            if (
                tool_def
                and "function" in tool_def
                and "parameters" in tool_def["function"]
            ):
                parameters = tool_def["function"]["parameters"]
                expected_args = parameters.get("properties", {})
                required_params = set(parameters.get("required", []))
            else:
                expected_args = {arg: {} for arg in tool_args.keys()}
                required_params = set()

            # Validate tool call arguments
            provided_args = set(tool_args.keys())
            expected_args_set = set(expected_args.keys())

            # Check for unexpected arguments (typos)
            unexpected_args = provided_args - expected_args_set
            # Only check for missing REQUIRED parameters
            missing_required_args = required_params - provided_args

            if unexpected_args or missing_required_args:
                error_msg = f"Tool call '{tool_name}' has parameter errors:"
                if unexpected_args:
                    error_msg += f" Unknown parameters: {sorted(unexpected_args)}."
                if missing_required_args:
                    error_msg += f" Missing required parameters: {sorted(missing_required_args)}."
                error_msg += f" Expected parameters: {sorted(expected_args_set)}."
                if required_params:
                    error_msg += f" Required parameters: {sorted(required_params)}."
                validation_errors_list.append(error_msg)

        if validation_errors_list:
            raise ValueError("; ".join(validation_errors_list))

        return resp