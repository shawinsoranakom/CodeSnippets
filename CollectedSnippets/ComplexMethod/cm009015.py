def _get_bound_model(
        request: ModelRequest[ContextT],
    ) -> tuple[Runnable[Any, Any], ResponseFormat[Any] | None]:
        """Get the model with appropriate tool bindings.

        Performs auto-detection of strategy if needed based on model capabilities.

        Args:
            request: The model request containing model, tools, and response format.

        Returns:
            Tuple of `(bound_model, effective_response_format)` where
            `effective_response_format` is the actual strategy used (may differ from
            initial if auto-detected).

        Raises:
            ValueError: If middleware returned unknown client-side tool names.
            ValueError: If `ToolStrategy` specifies tools not declared upfront.
        """
        # Validate ONLY client-side tools that need to exist in tool_node
        # Skip validation when wrap_tool_call is defined, as middleware may handle
        # dynamic tools that are added at runtime via wrap_model_call
        has_wrap_tool_call = wrap_tool_call_wrapper or awrap_tool_call_wrapper

        # Build map of available client-side tools from the ToolNode
        # (which has already converted callables)
        available_tools_by_name = {}
        if tool_node:
            available_tools_by_name = tool_node.tools_by_name.copy()

        # Check if any requested tools are unknown CLIENT-SIDE tools
        # Only validate if wrap_tool_call is NOT defined (no dynamic tool handling)
        if not has_wrap_tool_call:
            unknown_tool_names = []
            for t in request.tools:
                # Only validate BaseTool instances (skip built-in dict tools)
                if isinstance(t, dict):
                    continue
                if isinstance(t, BaseTool) and t.name not in available_tools_by_name:
                    unknown_tool_names.append(t.name)

            if unknown_tool_names:
                available_tool_names = sorted(available_tools_by_name.keys())
                msg = DYNAMIC_TOOL_ERROR_TEMPLATE.format(
                    unknown_tool_names=unknown_tool_names,
                    available_tool_names=available_tool_names,
                )
                raise ValueError(msg)

        # Normalize raw schemas to AutoStrategy
        # (handles middleware override with raw Pydantic classes)
        response_format: ResponseFormat[Any] | Any | None = request.response_format
        if response_format is not None and not isinstance(
            response_format, (AutoStrategy, ToolStrategy, ProviderStrategy)
        ):
            response_format = AutoStrategy(schema=response_format)

        # Determine effective response format (auto-detect if needed)
        effective_response_format: ResponseFormat[Any] | None
        if isinstance(response_format, AutoStrategy):
            # User provided raw schema via AutoStrategy - auto-detect best strategy based on model
            if _supports_provider_strategy(request.model, tools=request.tools):
                # Model supports provider strategy - use it
                effective_response_format = ProviderStrategy(schema=response_format.schema)
            elif response_format is initial_response_format and tool_strategy_for_setup is not None:
                # Model doesn't support provider strategy - use ToolStrategy
                # Reuse the strategy from setup if possible to preserve tool names
                effective_response_format = tool_strategy_for_setup
            else:
                effective_response_format = ToolStrategy(schema=response_format.schema)
        else:
            # User explicitly specified a strategy - preserve it
            effective_response_format = response_format

        # Build final tools list including structured output tools
        # request.tools now only contains BaseTool instances (converted from callables)
        # and dicts (built-ins)
        final_tools = list(request.tools)
        if isinstance(effective_response_format, ToolStrategy):
            # Add structured output tools to final tools list
            structured_tools = [info.tool for info in structured_output_tools.values()]
            final_tools.extend(structured_tools)

        # Bind model based on effective response format
        if isinstance(effective_response_format, ProviderStrategy):
            # (Backward compatibility) Use OpenAI format structured output
            kwargs = effective_response_format.to_model_kwargs()
            return (
                request.model.bind_tools(
                    final_tools, strict=True, **kwargs, **request.model_settings
                ),
                effective_response_format,
            )

        if isinstance(effective_response_format, ToolStrategy):
            # Current implementation requires that tools used for structured output
            # have to be declared upfront when creating the agent as part of the
            # response format. Middleware is allowed to change the response format
            # to a subset of the original structured tools when using ToolStrategy,
            # but not to add new structured tools that weren't declared upfront.
            # Compute output binding
            for tc in effective_response_format.schema_specs:
                if tc.name not in structured_output_tools:
                    msg = (
                        f"ToolStrategy specifies tool '{tc.name}' "
                        "which wasn't declared in the original "
                        "response format when creating the agent."
                    )
                    raise ValueError(msg)

            # Force tool use if we have structured output tools
            tool_choice = "any" if structured_output_tools else request.tool_choice
            return (
                request.model.bind_tools(
                    final_tools, tool_choice=tool_choice, **request.model_settings
                ),
                effective_response_format,
            )

        # No structured output - standard model binding
        if final_tools:
            return (
                request.model.bind_tools(
                    final_tools, tool_choice=request.tool_choice, **request.model_settings
                ),
                None,
            )
        return request.model.bind(**request.model_settings), None