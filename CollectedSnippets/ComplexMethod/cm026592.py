async def _async_handle_chat_log(  # noqa: C901
        self,
        chat_log: conversation.ChatLog,
        structure_name: str | None = None,
        structure: vol.Schema | None = None,
        max_iterations: int = MAX_TOOL_ITERATIONS,
    ) -> None:
        """Generate an answer for the chat log."""
        options = self.subentry.data

        preloaded_tools = [
            "HassTurnOn",
            "HassTurnOff",
            "GetLiveContext",
            "code_execution",
            "web_search",
        ]

        system = chat_log.content[0]
        if not isinstance(system, conversation.SystemContent):
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="system_message_not_found"
            )

        messages, container_id = _convert_content(chat_log.content[1:])

        model = options.get(CONF_CHAT_MODEL, DEFAULT[CONF_CHAT_MODEL])

        model_args = MessageCreateParamsStreaming(
            model=model,
            messages=messages,
            max_tokens=options.get(CONF_MAX_TOKENS, DEFAULT[CONF_MAX_TOKENS]),
            system=system.content,
            stream=True,
            container=container_id,
        )

        if (
            options.get(CONF_PROMPT_CACHING, DEFAULT[CONF_PROMPT_CACHING])
            == PromptCaching.PROMPT
        ):
            model_args["system"] = [
                {
                    "type": "text",
                    "text": system.content,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        elif (
            options.get(CONF_PROMPT_CACHING, DEFAULT[CONF_PROMPT_CACHING])
            == PromptCaching.AUTOMATIC
        ):
            model_args["cache_control"] = {"type": "ephemeral"}

        if (
            self.model_info.capabilities
            and self.model_info.capabilities.thinking.types.adaptive.supported
        ):
            thinking_effort = options.get(
                CONF_THINKING_EFFORT, DEFAULT[CONF_THINKING_EFFORT]
            )
            if thinking_effort != "none":
                model_args["thinking"] = ThinkingConfigAdaptiveParam(
                    type="adaptive", display="summarized"
                )
                model_args["output_config"] = OutputConfigParam(effort=thinking_effort)
            else:
                model_args["thinking"] = ThinkingConfigDisabledParam(type="disabled")
        else:
            thinking_budget = options.get(
                CONF_THINKING_BUDGET, DEFAULT[CONF_THINKING_BUDGET]
            )
            if (
                self.model_info.capabilities
                and self.model_info.capabilities.thinking.types.enabled.supported
                and thinking_budget >= MIN_THINKING_BUDGET
            ):
                model_args["thinking"] = ThinkingConfigEnabledParam(
                    type="enabled", display="summarized", budget_tokens=thinking_budget
                )
            else:
                model_args["thinking"] = ThinkingConfigDisabledParam(type="disabled")

            if (
                self.model_info.capabilities
                and self.model_info.capabilities.effort.supported
            ):
                model_args["output_config"] = OutputConfigParam(
                    effort=options.get(
                        CONF_THINKING_EFFORT, DEFAULT[CONF_THINKING_EFFORT]
                    )
                )

        tools: list[ToolUnionParam] = []
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        if options.get(CONF_CODE_EXECUTION):
            # The `web_search_20260209` tool automatically enables `code_execution_20260120` tool
            if (
                not self.model_info.capabilities
                or not self.model_info.capabilities.code_execution.supported
                or not options.get(CONF_WEB_SEARCH)
            ):
                tools.append(
                    CodeExecutionTool20250825Param(
                        name="code_execution",
                        type="code_execution_20250825",
                    ),
                )

        if options.get(CONF_WEB_SEARCH):
            if (
                not self.model_info.capabilities
                or not self.model_info.capabilities.code_execution.supported
                or not options.get(CONF_CODE_EXECUTION)
            ):
                web_search: WebSearchTool20250305Param | WebSearchTool20260209Param = (
                    WebSearchTool20250305Param(
                        name="web_search",
                        type="web_search_20250305",
                        max_uses=options.get(CONF_WEB_SEARCH_MAX_USES),
                    )
                )
            else:
                web_search = WebSearchTool20260209Param(
                    name="web_search",
                    type="web_search_20260209",
                    max_uses=options.get(CONF_WEB_SEARCH_MAX_USES),
                )
            if options.get(CONF_WEB_SEARCH_USER_LOCATION):
                web_search["user_location"] = {
                    "type": "approximate",
                    "city": options.get(CONF_WEB_SEARCH_CITY, ""),
                    "region": options.get(CONF_WEB_SEARCH_REGION, ""),
                    "country": options.get(CONF_WEB_SEARCH_COUNTRY, ""),
                    "timezone": options.get(CONF_WEB_SEARCH_TIMEZONE, ""),
                }
            tools.append(web_search)

        # Handle attachments by adding them to the last user message
        last_content = chat_log.content[-1]
        if last_content.role == "user" and last_content.attachments:
            last_message = messages[-1]
            if last_message["role"] != "user":
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="user_message_not_found"
                )
            if isinstance(last_message["content"], str):
                last_message["content"] = [
                    TextBlockParam(type="text", text=last_message["content"])
                ]
            last_message["content"].extend(  # type: ignore[union-attr]
                await async_prepare_files_for_prompt(
                    self.hass,
                    self.model_info,
                    [(a.path, a.mime_type) for a in last_content.attachments],
                )
            )

        if structure and structure_name:
            if (
                self.model_info.capabilities
                and self.model_info.capabilities.structured_outputs.supported
            ):
                # Native structured output for those models who support it.
                structure_name = None
                model_args.setdefault("output_config", OutputConfigParam())[
                    "format"
                ] = JSONOutputFormatParam(
                    type="json_schema",
                    schema={
                        **convert(
                            structure,
                            custom_serializer=chat_log.llm_api.custom_serializer
                            if chat_log.llm_api
                            else llm.selector_serializer,
                        ),
                        "additionalProperties": False,
                    },
                )
            elif model_args["thinking"]["type"] == "disabled":
                structure_name = slugify(structure_name)
                if not tools:
                    # Simplest case: no tools and no extended thinking
                    # Add a tool and force its use
                    model_args["tool_choice"] = ToolChoiceToolParam(
                        type="tool",
                        name=structure_name,
                    )
                else:
                    # Second case: tools present but no extended thinking
                    # Allow the model to use any tool but not text response
                    # The model should know to use the right tool by its description
                    model_args["tool_choice"] = ToolChoiceAnyParam(
                        type="any",
                    )
            else:
                # Extended thinking is enabled. With extended thinking, we cannot
                # force tool use or disable text responses, so we add a hint to the
                # system prompt instead. With extended thinking, the model should be
                # smart enough to use the tool.
                structure_name = slugify(structure_name)
                model_args["tool_choice"] = ToolChoiceAutoParam(
                    type="auto",
                )

                model_args["system"].append(  # type: ignore[union-attr]
                    TextBlockParam(
                        type="text",
                        text=f"Claude MUST use the '{structure_name}' tool to provide "
                        "the final answer instead of plain text.",
                    )
                )

            if structure_name:
                tools.append(
                    ToolParam(
                        name=structure_name,
                        description="Use this tool to reply to the user",
                        input_schema=convert(
                            structure,
                            custom_serializer=chat_log.llm_api.custom_serializer
                            if chat_log.llm_api
                            else llm.selector_serializer,
                        ),
                    )
                )
                preloaded_tools.append(structure_name)

        if tools:
            if (
                options.get(CONF_TOOL_SEARCH, DEFAULT[CONF_TOOL_SEARCH])
                and len(tools) > len(preloaded_tools) + 1
            ):
                for tool in tools:
                    if not tool["name"].endswith(tuple(preloaded_tools)):
                        tool["defer_loading"] = True
                tools.append(
                    ToolSearchToolBm25_20251119Param(
                        type="tool_search_tool_bm25_20251119",
                        name="tool_search_tool_bm25",
                    )
                )

            model_args["tools"] = tools

        coordinator = self.entry.runtime_data
        client = coordinator.client

        # To prevent infinite loops, we limit the number of iterations
        for _iteration in range(max_iterations):
            try:
                stream = await client.messages.create(**model_args)

                new_messages, model_args["container"] = _convert_content(
                    [
                        content
                        async for content in chat_log.async_add_delta_content_stream(
                            self.entity_id,
                            _transform_stream(
                                chat_log,
                                stream,
                                output_tool=structure_name or None,
                            ),
                        )
                    ]
                )
                messages.extend(new_messages)
            except anthropic.AuthenticationError as err:
                # Trigger coordinator to confirm the auth failure and trigger the reauth flow.
                await coordinator.async_request_refresh()
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="api_authentication_error",
                    translation_placeholders={"message": err.message},
                ) from err
            except anthropic.APIConnectionError as err:
                LOGGER.info("Connection error while talking to Anthropic: %s", err)
                coordinator.mark_connection_error()
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="api_error",
                    translation_placeholders={"message": err.message},
                ) from err
            except anthropic.AnthropicError as err:
                # Non-connection error, mark connection as healthy
                coordinator.async_set_updated_data(coordinator.data)
                LOGGER.error("Error while talking to Anthropic: %s", err)
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="api_error",
                    translation_placeholders={
                        "message": err.message
                        if isinstance(err, anthropic.APIError)
                        else str(err)
                    },
                ) from err

            if not chat_log.unresponded_tool_results:
                coordinator.async_set_updated_data(coordinator.data)
                break