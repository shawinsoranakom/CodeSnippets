async def run(
        self,
        input_data: Input,
        *,
        credentials: llm.APIKeyCredentials,
        graph_id: str,
        node_id: str,
        graph_exec_id: str,
        node_exec_id: str,
        user_id: str,
        graph_version: int,
        execution_context: ExecutionContext,
        execution_processor: "ExecutionProcessor",
        nodes_to_skip: set[str] | None = None,
        **kwargs,
    ) -> BlockOutput:

        tool_functions = await self._create_tool_node_signatures(node_id)
        original_tool_count = len(tool_functions)

        # Filter out tools for nodes that should be skipped (e.g., missing optional credentials)
        if nodes_to_skip:
            tool_functions = [
                tf
                for tf in tool_functions
                if tf.get("function", {}).get("_sink_node_id") not in nodes_to_skip
            ]

            # Only raise error if we had tools but they were all filtered out
            if original_tool_count > 0 and not tool_functions:
                raise ValueError(
                    "No available tools to execute - all downstream nodes are unavailable "
                    "(possibly due to missing optional credentials)"
                )

        yield "tool_functions", json.dumps(tool_functions)

        conversation_history = input_data.conversation_history or []
        prompt = [json.to_dict(p) for p in conversation_history if p]

        pending_tool_calls = get_pending_tool_calls(conversation_history)
        if pending_tool_calls and input_data.last_tool_output is None:
            raise ValueError(f"Tool call requires an output for {pending_tool_calls}")

        use_responses_api = input_data.model.metadata.provider == "openai"

        tool_output = []
        if pending_tool_calls and input_data.last_tool_output is not None:
            first_call_id = next(iter(pending_tool_calls.keys()))
            tool_output.append(
                _create_tool_response(
                    first_call_id,
                    input_data.last_tool_output,
                    responses_api=use_responses_api,
                )
            )

            prompt.extend(tool_output)
            remaining_pending_calls = get_pending_tool_calls(prompt)

            if remaining_pending_calls:
                yield "conversations", prompt
                return
        elif input_data.last_tool_output:
            logger.error(
                f"[OrchestratorBlock-node_exec_id={node_exec_id}] "
                f"No pending tool calls found. This may indicate an issue with the "
                f"conversation history, or the tool giving response more than once."
                f"This should not happen! Please check the conversation history for any inconsistencies."
            )
            tool_output.append(
                {
                    "role": "user",
                    "content": f"Last tool output: {json.dumps(input_data.last_tool_output)}",
                }
            )
            prompt.extend(tool_output)

        values = input_data.prompt_values
        if values:
            input_data.prompt = await llm.fmt.format_string(input_data.prompt, values)
            input_data.sys_prompt = await llm.fmt.format_string(
                input_data.sys_prompt, values
            )

        if input_data.sys_prompt and not any(
            p.get("role") == "system"
            and isinstance(p.get("content"), str)
            and p["content"].startswith(MAIN_OBJECTIVE_PREFIX)
            for p in prompt
        ):
            prompt.append(
                {
                    "role": "system",
                    "content": MAIN_OBJECTIVE_PREFIX + input_data.sys_prompt,
                }
            )

        if input_data.prompt and not any(
            p.get("role") == "user"
            and isinstance(p.get("content"), str)
            and p["content"].startswith(MAIN_OBJECTIVE_PREFIX)
            for p in prompt
        ):
            prompt.append(
                {"role": "user", "content": MAIN_OBJECTIVE_PREFIX + input_data.prompt}
            )

        # Execute tools based on the selected mode
        if input_data.execution_mode == ExecutionMode.EXTENDED_THINKING:
            # Validate — Claude Code SDK only works with Claude models
            provider = input_data.model.metadata.provider
            model_name = input_data.model.value
            # All Claude models have metadata.provider == "anthropic", but
            # "open_router" is included defensively in case future models
            # use a different metadata provider for the same Anthropic API.
            if provider not in ("anthropic", "open_router"):
                raise ValueError(
                    f"Claude Code SDK mode requires an Anthropic-compatible "
                    f"provider (got provider={provider}). "
                    "Please select an Anthropic or OpenRouter provider, "
                    "or switch execution mode to 'built_in'."
                )
            # Safety-net: all Claude models have .value starting with "claude-".
            # This guards against non-Claude models that happen to use the
            # "anthropic" metadata provider (if any are added in the future).
            if not model_name.startswith("claude"):
                raise ValueError(
                    f"Claude Code SDK mode only supports Claude models "
                    f"(got model={model_name}). "
                    "Please select a Claude model, "
                    "or switch execution mode to 'built_in'."
                )
            # Claude Code SDK: SDK manages conversation + tool calling
            execution_params = ExecutionParams(
                user_id=user_id,
                graph_id=graph_id,
                node_id=node_id,
                graph_version=graph_version,
                graph_exec_id=graph_exec_id,
                node_exec_id=node_exec_id,
                execution_context=execution_context,
            )
            async for result in self._execute_tools_sdk_mode(
                input_data=input_data,
                credentials=credentials,
                tool_functions=tool_functions,
                prompt=prompt,
                execution_params=execution_params,
                execution_processor=execution_processor,
            ):
                yield result
            return

        if input_data.agent_mode_max_iterations != 0:
            # In agent mode, execute tools directly in a loop until finished
            async for result in self._execute_tools_agent_mode(
                input_data=input_data,
                credentials=credentials,
                tool_functions=tool_functions,
                prompt=prompt,
                graph_exec_id=graph_exec_id,
                node_id=node_id,
                node_exec_id=node_exec_id,
                user_id=user_id,
                graph_id=graph_id,
                graph_version=graph_version,
                execution_context=execution_context,
                execution_processor=execution_processor,
            ):
                yield result
            return

        # One-off mode: single LLM call and yield tool calls for external execution
        current_prompt = list(prompt)
        max_attempts = max(1, int(input_data.retry))
        response = None

        last_error = None
        for _ in range(max_attempts):
            try:
                response = await self._attempt_llm_call_with_validation(
                    credentials, input_data, current_prompt, tool_functions
                )
                break

            except ValueError as e:
                last_error = e
                error_feedback = (
                    "Your tool call had errors. Please fix the following issues and try again:\n"
                    + f"- {str(e)}\n"
                    + "\nPlease make sure to use the exact tool and parameter names as specified in the function schema."
                )
                current_prompt = list(current_prompt) + [
                    {"role": "user", "content": error_feedback}
                ]

        if response is None:
            raise last_error or ValueError(
                "Failed to get valid response after all retry attempts"
            )

        if not response.tool_calls:
            yield "finished", response.response
            return

        for tool_call in response.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            tool_def = next(
                (
                    tool
                    for tool in tool_functions
                    if tool["function"]["name"] == tool_name
                ),
                None,
            )
            if not tool_def:
                # NOTE: This matches the logic in _attempt_llm_call_with_validation and
                # relies on its validation for the assumption that this is valid to use.
                if len(tool_functions) == 1:
                    tool_def = tool_functions[0]
                else:
                    # This should not happen due to prior validation
                    continue

            if "function" in tool_def and "parameters" in tool_def["function"]:
                expected_args = tool_def["function"]["parameters"].get("properties", {})
            else:
                expected_args = {arg: {} for arg in tool_args.keys()}

            # Get the sink node ID and field mapping from tool definition
            field_mapping = tool_def["function"].get("_field_mapping", {})
            sink_node_id = tool_def["function"]["_sink_node_id"]

            for clean_arg_name in expected_args:
                # arg_name is now always the cleaned field name (for Anthropic API compliance)
                # Get the original field name from field mapping for proper emit key generation
                original_field_name = field_mapping.get(clean_arg_name, clean_arg_name)
                arg_value = tool_args.get(clean_arg_name)

                # Use original_field_name directly (not sanitized) to match link sink_name
                # The field_mapping already translates from LLM's cleaned names to original names
                emit_key = f"tools_^_{sink_node_id}_~_{original_field_name}"

                logger.debug(
                    "[OrchestratorBlock|geid:%s|neid:%s] emit %s",
                    graph_exec_id,
                    node_exec_id,
                    emit_key,
                )
                yield emit_key, arg_value

        converted = _convert_raw_response_to_dict(response.raw_response)

        # Check for tool calls to avoid inserting reasoning between tool pairs
        if isinstance(converted, list):
            has_tool_calls = any(
                item.get("type") == "function_call" for item in converted
            )
        else:
            has_tool_calls = isinstance(converted.get("content"), list) and any(
                item.get("type") == "tool_use" for item in converted.get("content", [])
            )

        if response.reasoning and not has_tool_calls:
            prompt.append(
                {"role": "assistant", "content": f"[Reasoning]: {response.reasoning}"}
            )

        if isinstance(converted, list):
            prompt.extend(converted)
        else:
            prompt.append(converted)

        yield "conversations", prompt