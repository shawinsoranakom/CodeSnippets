async def create_chat_completion(
        self,
        model_prompt: list[ChatMessage],
        model_name: AnthropicModelName,
        completion_parser: Callable[[AssistantChatMessage], _T] = lambda _: None,
        functions: Optional[list[CompletionModelFunction]] = None,
        max_output_tokens: Optional[int] = None,
        prefill_response: str = "",
        **kwargs,
    ) -> ChatModelResponse[_T]:
        """Create a completion using the Anthropic API."""
        anthropic_messages, completion_kwargs = self._get_chat_completion_args(
            prompt_messages=model_prompt,
            functions=functions,
            max_output_tokens=max_output_tokens,
            **kwargs,
        )

        total_cost = 0.0
        attempts = 0
        while True:
            completion_kwargs["messages"] = anthropic_messages.copy()
            if prefill_response:
                completion_kwargs["messages"].append(
                    {"role": "assistant", "content": prefill_response}
                )

            (
                _assistant_msg,
                cost,
                t_input,
                t_output,
            ) = await self._create_chat_completion(model_name, completion_kwargs)
            total_cost += cost
            self._logger.debug(
                f"Completion usage: {t_input} input, {t_output} output "
                f"- ${round(cost, 5)}"
            )

            # Merge prefill into generated response
            if prefill_response:
                first_text_block = next(
                    b for b in _assistant_msg.content if b.type == "text"
                )
                first_text_block.text = prefill_response + first_text_block.text

            assistant_msg = AssistantChatMessage(
                content="\n\n".join(
                    b.text for b in _assistant_msg.content if b.type == "text"
                ),
                tool_calls=self._parse_assistant_tool_calls(_assistant_msg),
            )

            # If parsing the response fails, append the error to the prompt, and let the
            # LLM fix its mistake(s).
            attempts += 1
            tool_call_errors = []
            try:
                # Validate tool calls
                if assistant_msg.tool_calls and functions:
                    tool_call_errors = validate_tool_calls(
                        assistant_msg.tool_calls, functions
                    )
                    if tool_call_errors:
                        raise ValueError(
                            "Invalid tool use(s):\n"
                            + "\n".join(str(e) for e in tool_call_errors)
                        )

                parsed_result = completion_parser(assistant_msg)
                break
            except Exception as e:
                self._logger.debug(
                    f"Parsing failed on response: '''{_assistant_msg}'''"
                )
                self._logger.warning(f"Parsing attempt #{attempts} failed: {e}")
                sentry_sdk.capture_exception(
                    error=e,
                    extras={"assistant_msg": _assistant_msg, "i_attempt": attempts},
                )
                if attempts < self._configuration.fix_failed_parse_tries:
                    anthropic_messages.append(
                        _assistant_msg.model_dump(include={"role", "content"})  # type: ignore # noqa
                    )

                    # Build tool_result blocks for each tool call
                    # (required if last assistant message had tool_use blocks)
                    tool_results = []
                    for tc in assistant_msg.tool_calls or []:
                        error_msg = self._get_tool_error_message(
                            tc, tool_call_errors, functions
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tc.id,
                                "is_error": True,
                                "content": [{"type": "text", "text": error_msg}],
                            }
                        )

                    anthropic_messages.append(
                        {
                            "role": "user",
                            "content": [
                                *tool_results,
                                {
                                    "type": "text",
                                    "text": (
                                        f"ERROR PARSING YOUR RESPONSE:\n\n"
                                        f"{e.__class__.__name__}: {e}"
                                    ),
                                },
                            ],
                        }
                    )
                else:
                    raise

        if attempts > 1:
            self._logger.debug(
                f"Total cost for {attempts} attempts: ${round(total_cost, 5)}"
            )

        return ChatModelResponse(
            response=assistant_msg,
            parsed_result=parsed_result,
            llm_info=ANTHROPIC_CHAT_MODELS[model_name],
            prompt_tokens_used=t_input,
            completion_tokens_used=t_output,
        )