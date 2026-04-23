async def create_chat_completion(
        self,
        model_prompt: list[ChatMessage],
        model_name: _ModelName,
        completion_parser: Callable[[AssistantChatMessage], _T] = lambda _: None,
        functions: Optional[list[CompletionModelFunction]] = None,
        max_output_tokens: Optional[int] = None,
        prefill_response: str = "",
        **kwargs,
    ) -> ChatModelResponse[_T]:
        """Create a chat completion using the API."""

        (
            openai_messages,
            completion_kwargs,
            parse_kwargs,
        ) = self._get_chat_completion_args(
            prompt_messages=model_prompt,
            model=model_name,
            functions=functions,
            max_output_tokens=max_output_tokens,
            **kwargs,
        )

        total_cost = 0.0
        attempts = 0
        while True:
            completion_kwargs["messages"] = openai_messages
            _response, _cost, t_input, t_output = await self._create_chat_completion(
                model=model_name,
                completion_kwargs=completion_kwargs,
            )
            total_cost += _cost

            # If parsing the response fails, append the error to the prompt, and let the
            # LLM fix its mistake(s).
            attempts += 1
            parse_errors: list[Exception] = []

            _assistant_msg = _response.choices[0].message

            tool_calls, _errors = self._parse_assistant_tool_calls(
                _assistant_msg, **parse_kwargs
            )
            parse_errors += _errors

            # Validate tool calls
            if not parse_errors and tool_calls and functions:
                parse_errors += validate_tool_calls(tool_calls, functions)

            assistant_msg = AssistantChatMessage(
                content=_assistant_msg.content or "",
                tool_calls=tool_calls or None,
            )

            parsed_result: _T = None  # type: ignore
            if not parse_errors:
                try:
                    parsed_result = completion_parser(assistant_msg)
                except Exception as e:
                    parse_errors.append(e)

            if not parse_errors:
                if attempts > 1:
                    self._logger.debug(
                        f"Total cost for {attempts} attempts: ${round(total_cost, 5)}"
                    )

                return ChatModelResponse(
                    response=AssistantChatMessage(
                        content=_assistant_msg.content or "",
                        tool_calls=tool_calls or None,
                    ),
                    parsed_result=parsed_result,
                    llm_info=self.CHAT_MODELS[model_name],
                    prompt_tokens_used=t_input,
                    completion_tokens_used=t_output,
                )

            else:
                self._logger.debug(
                    f"Parsing failed on response: '''{_assistant_msg}'''"
                )
                parse_errors_fmt = self._format_parse_errors(
                    parse_errors, tool_calls, functions
                )
                self._logger.warning(
                    f"Parsing attempt #{attempts} failed: {parse_errors_fmt}"
                )
                for e in parse_errors:
                    sentry_sdk.capture_exception(
                        error=e,
                        extras={"assistant_msg": _assistant_msg, "i_attempt": attempts},
                    )

                if attempts < self._configuration.fix_failed_parse_tries:
                    # Strip tool_calls from the assistant message before
                    # appending, otherwise OpenAI will reject the next
                    # request because there are no tool response messages
                    # following the tool_calls.
                    # Ensure content is always a string (not null/missing)
                    # since OpenAI requires it on assistant messages.
                    retry_msg = _assistant_msg.model_dump(exclude_none=True)
                    retry_msg.pop("tool_calls", None)
                    if not retry_msg.get("content"):
                        retry_msg["content"] = ""
                    openai_messages.append(
                        cast(
                            ChatCompletionAssistantMessageParam,
                            retry_msg,
                        )
                    )
                    openai_messages.append(
                        {
                            "role": "system",
                            "content": (
                                f"ERROR PARSING YOUR RESPONSE:\n\n{parse_errors_fmt}"
                            ),
                        }
                    )
                    continue
                else:
                    raise parse_errors[0]