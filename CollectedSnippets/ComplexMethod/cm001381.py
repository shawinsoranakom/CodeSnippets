def _get_chat_completion_args(
        self,
        prompt_messages: list[ChatMessage],
        functions: Optional[list[CompletionModelFunction]] = None,
        max_output_tokens: Optional[int] = None,
        thinking_budget_tokens: Optional[int] = None,
        **kwargs,
    ) -> tuple[list[MessageParam], MessageCreateParams]:
        """Prepare arguments for message completion API call.

        Args:
            prompt_messages: List of ChatMessages.
            functions: Optional list of functions available to the LLM.
            max_output_tokens: Maximum number of output tokens.
            thinking_budget_tokens: Token budget for extended thinking (min 1024).
            kwargs: Additional keyword arguments.

        Returns:
            list[MessageParam]: Prompt messages for the Anthropic call
            dict[str, Any]: Any other kwargs for the Anthropic call
        """
        if functions:
            kwargs["tools"] = [
                {
                    "name": f.name,
                    "description": f.description,
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            name: param.to_dict()
                            for name, param in f.parameters.items()
                        },
                        "required": [
                            name
                            for name, param in f.parameters.items()
                            if param.required
                        ],
                    },
                }
                for f in functions
            ]

        kwargs["max_tokens"] = max_output_tokens or 4096

        # Handle extended thinking if enabled
        if thinking_budget_tokens is not None and thinking_budget_tokens > 0:
            # Minimum budget is 1024 tokens per Anthropic's API requirements
            budget = max(thinking_budget_tokens, 1024)
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }
            # Add beta header for interleaved thinking with tool use
            if functions:
                kwargs["extra_headers"] = kwargs.get("extra_headers", {})
                kwargs["extra_headers"][
                    "anthropic-beta"
                ] = "interleaved-thinking-2025-05-14"

        if extra_headers := self._configuration.extra_request_headers:
            kwargs["extra_headers"] = kwargs.get("extra_headers", {})
            kwargs["extra_headers"].update(extra_headers.copy())

        system_messages = [
            m for m in prompt_messages if m.role == ChatMessage.Role.SYSTEM
        ]
        if (_n := len(system_messages)) > 1:
            self._logger.warning(
                f"Prompt has {_n} system messages; Anthropic supports only 1. "
                "They will be merged, and removed from the rest of the prompt."
            )
        kwargs["system"] = "\n\n".join(sm.content for sm in system_messages)

        messages: list[MessageParam] = []
        for message in prompt_messages:
            if message.role == ChatMessage.Role.SYSTEM:
                continue
            elif message.role == ChatMessage.Role.USER:
                # Merge subsequent user messages
                if messages and (prev_msg := messages[-1])["role"] == "user":
                    if isinstance(prev_msg["content"], str):
                        prev_msg["content"] += f"\n\n{message.content}"
                    else:
                        assert isinstance(prev_msg["content"], list)
                        prev_msg["content"].append(
                            {"type": "text", "text": message.content}
                        )
                else:
                    messages.append({"role": "user", "content": message.content})
                # TODO: add support for image blocks
            elif message.role == ChatMessage.Role.ASSISTANT:
                if isinstance(message, AssistantChatMessage) and message.tool_calls:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": [
                                *(
                                    [{"type": "text", "text": message.content}]
                                    if message.content
                                    else []
                                ),
                                *(
                                    {
                                        "type": "tool_use",
                                        "id": tc.id,
                                        "name": tc.function.name,
                                        "input": tc.function.arguments,
                                    }
                                    for tc in message.tool_calls
                                ),
                            ],
                        }
                    )
                elif message.content:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": message.content,
                        }
                    )
            elif isinstance(message, ToolResultMessage):
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message.tool_call_id,
                                "content": [{"type": "text", "text": message.content}],
                                "is_error": message.is_error,
                            }
                        ],
                    }
                )

        return messages, kwargs