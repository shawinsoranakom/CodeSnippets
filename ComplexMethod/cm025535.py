async def _async_handle_chat_log(
        self,
        type: Literal["ai_task", "conversation"],
        chat_log: conversation.ChatLog,
        structure_name: str | None = None,
        structure: vol.Schema | None = None,
    ) -> None:
        """Generate a response for the chat log."""

        for _ in range(_MAX_TOOL_ITERATIONS):
            response_format: dict[str, Any] | None = None
            if structure and structure_name:
                response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": slugify(structure_name),
                        "schema": _format_structured_output(
                            structure, chat_log.llm_api
                        ),
                        "strict": False,
                    },
                }

            messages = _convert_content_to_param(chat_log.content)

            response_kwargs = await self._prepare_chat_for_generation(
                chat_log,
                messages,
                response_format,
            )

            try:
                if type == "conversation":
                    raw_stream = await self._cloud.llm.async_process_conversation(
                        **response_kwargs,
                    )
                else:
                    raw_stream = await self._cloud.llm.async_generate_data(
                        **response_kwargs,
                    )

                messages.extend(
                    _convert_content_to_param(
                        [
                            content
                            async for content in chat_log.async_add_delta_content_stream(
                                self.entity_id,
                                _transform_stream(
                                    chat_log,
                                    raw_stream,
                                    True,
                                ),
                            )
                        ]
                    )
                )

            except LLMAuthenticationError as err:
                raise HomeAssistantError("Cloud LLM authentication failed") from err
            except LLMRateLimitError as err:
                raise HomeAssistantError("Cloud LLM is rate limited") from err
            except LLMResponseError as err:
                raise HomeAssistantError(str(err)) from err
            except LLMServiceError as err:
                raise HomeAssistantError("Error talking to Cloud LLM") from err
            except NabuCasaBaseError as err:
                raise HomeAssistantError(str(err)) from err

            if not chat_log.unresponded_tool_results:
                break