async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure_name: str | None = None,
        structure: vol.Schema | None = None,
        force_image: bool = False,
        max_iterations: int = MAX_TOOL_ITERATIONS,
    ) -> None:
        """Generate an answer for the chat log."""
        options = self.subentry.data

        messages = _convert_content_to_param(chat_log.content)

        model_args = ResponseCreateParamsStreaming(
            model=options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
            input=messages,
            max_output_tokens=options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
            user=chat_log.conversation_id,
            service_tier=options.get(CONF_SERVICE_TIER, RECOMMENDED_SERVICE_TIER),
            store=options.get(CONF_STORE_RESPONSES, RECOMMENDED_STORE_RESPONSES),
            stream=True,
        )

        if model_args["model"].startswith(("o", "gpt-5")):
            model_args["reasoning"] = {
                "effort": options.get(
                    CONF_REASONING_EFFORT, RECOMMENDED_REASONING_EFFORT
                )
                if not model_args["model"].startswith("gpt-5-pro")
                else "high",  # GPT-5 pro only supports reasoning.effort: high
                "summary": options.get(
                    CONF_REASONING_SUMMARY, RECOMMENDED_REASONING_SUMMARY
                ),
            }
            model_args["include"] = ["reasoning.encrypted_content"]

        if (
            not model_args["model"].startswith("gpt-5")
            or model_args["reasoning"]["effort"] == "none"  # type: ignore[index]
        ):
            model_args["top_p"] = options.get(CONF_TOP_P, RECOMMENDED_TOP_P)
            model_args["temperature"] = options.get(
                CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE
            )

        if model_args["model"].startswith("gpt-5"):
            model_args["text"] = {
                "verbosity": options.get(CONF_VERBOSITY, RECOMMENDED_VERBOSITY)
            }

        if not model_args["model"].startswith(
            tuple(UNSUPPORTED_EXTENDED_CACHE_RETENTION_MODELS)
        ):
            model_args["prompt_cache_retention"] = "24h"

        tools: list[ToolParam] = []
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        remove_citations = False
        if options.get(CONF_WEB_SEARCH):
            web_search = WebSearchToolParam(
                type="web_search",
                search_context_size=options.get(
                    CONF_WEB_SEARCH_CONTEXT_SIZE, RECOMMENDED_WEB_SEARCH_CONTEXT_SIZE
                ),
            )
            if options.get(CONF_WEB_SEARCH_USER_LOCATION):
                web_search["user_location"] = UserLocation(
                    type="approximate",
                    city=options.get(CONF_WEB_SEARCH_CITY, ""),
                    region=options.get(CONF_WEB_SEARCH_REGION, ""),
                    country=options.get(CONF_WEB_SEARCH_COUNTRY, ""),
                    timezone=options.get(CONF_WEB_SEARCH_TIMEZONE, ""),
                )
            if not options.get(
                CONF_WEB_SEARCH_INLINE_CITATIONS,
                RECOMMENDED_WEB_SEARCH_INLINE_CITATIONS,
            ):
                system_message = cast(EasyInputMessageParam, messages[0])
                content = system_message["content"]
                if isinstance(content, str):
                    system_message["content"] = [
                        ResponseInputTextParam(type="input_text", text=content)
                    ]
                system_message["content"].append(  # type: ignore[union-attr]
                    ResponseInputTextParam(
                        type="input_text",
                        text="When doing a web search, do not include source citations",
                    )
                )

                if "reasoning" not in model_args:
                    # Reasoning models handle this correctly with just a prompt
                    remove_citations = True

            tools.append(web_search)

        if options.get(CONF_CODE_INTERPRETER):
            tools.append(
                CodeInterpreter(
                    type="code_interpreter",
                    container=CodeInterpreterContainerCodeInterpreterToolAuto(
                        type="auto"
                    ),
                )
            )
            model_args.setdefault("include", []).append("code_interpreter_call.outputs")  # type: ignore[union-attr]

        if force_image:
            image_model = options.get(CONF_IMAGE_MODEL, RECOMMENDED_IMAGE_MODEL)
            image_tool = ImageGeneration(
                type="image_generation",
                model=image_model,
                output_format="png",
            )
            if image_model not in ("gpt-image-1-mini", "gpt-image-2"):
                image_tool["input_fidelity"] = "high"
            tools.append(image_tool)
            # Keep image state on OpenAI so follow-up prompts can continue by
            # conversation ID without resending the generated image data.
            model_args["store"] = True
            model_args["tool_choice"] = ToolChoiceTypesParam(type="image_generation")

        if tools:
            model_args["tools"] = tools

        last_content = chat_log.content[-1]

        # Handle attachments by adding them to the last user message
        if last_content.role == "user" and last_content.attachments:
            files = await async_prepare_files_for_prompt(
                self.hass,
                [(a.path, a.mime_type) for a in last_content.attachments],
            )
            last_message = messages[-1]
            assert (
                last_message["type"] == "message"
                and last_message["role"] == "user"
                and isinstance(last_message["content"], str)
            )
            last_message["content"] = [
                {"type": "input_text", "text": last_message["content"]},
                *files,
            ]

        if structure and structure_name:
            model_args["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": slugify(structure_name),
                    "schema": _format_structured_output(structure, chat_log.llm_api),
                },
            }

        client = self.entry.runtime_data

        # To prevent infinite loops, we limit the number of iterations
        for _iteration in range(max_iterations):
            try:
                stream = await client.responses.create(**model_args)

                messages.extend(
                    _convert_content_to_param(
                        [
                            content
                            async for content in chat_log.async_add_delta_content_stream(
                                self.entity_id,
                                _transform_stream(chat_log, stream, remove_citations),
                            )
                        ]
                    )
                )
            except openai.RateLimitError as err:
                if (
                    model_args["service_tier"] == "flex"
                    and "resource unavailable" in (err.message or "").lower()
                ):
                    LOGGER.info(
                        "Flex tier is not available at the moment, continuing with default tier"
                    )
                    model_args["service_tier"] = "default"
                    continue
                LOGGER.error("Rate limited by OpenAI: %s", err)
                raise HomeAssistantError("Rate limited or insufficient funds") from err
            except openai.OpenAIError as err:
                if (
                    isinstance(err, openai.APIError)
                    and err.type == "insufficient_quota"
                ):
                    LOGGER.error("Insufficient funds for OpenAI: %s", err)
                    raise HomeAssistantError("Insufficient funds for OpenAI") from err
                if "Verify Organization" in str(err):
                    ir.async_create_issue(
                        self.hass,
                        DOMAIN,
                        "organization_verification_required",
                        is_fixable=False,
                        is_persistent=False,
                        learn_more_url="https://help.openai.com/en/articles/10910291-api-organization-verification",
                        severity=ir.IssueSeverity.WARNING,
                        translation_key="organization_verification_required",
                        translation_placeholders={
                            "platform_settings": "https://platform.openai.com/settings/organization/general"
                        },
                    )

                LOGGER.error("Error talking to OpenAI: %s", err)
                raise HomeAssistantError("Error talking to OpenAI") from err

            if not chat_log.unresponded_tool_results:
                break