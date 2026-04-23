def _get_chat_completion_args(
        self,
        prompt_messages: list[ChatMessage],
        model: _ModelName,
        functions: Optional[list[CompletionModelFunction]] = None,
        max_output_tokens: Optional[int] = None,
        reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
        **kwargs,
    ) -> tuple[
        list[ChatCompletionMessageParam], CompletionCreateParams, dict[str, Any]
    ]:
        """Prepare keyword arguments for a chat completion API call

        Args:
            prompt_messages: List of ChatMessages
            model: The model to use
            functions (optional): List of functions available to the LLM
            max_output_tokens (optional): Maximum number of tokens to generate
            reasoning_effort (optional): Reasoning effort for o-series and GPT-5 models

        Returns:
            list[ChatCompletionMessageParam]: Prompt messages for the API call
            CompletionCreateParams: Mapping of other kwargs for the API call
            Mapping[str, Any]: Any keyword arguments to pass on to the completion parser
        """
        kwargs = cast(CompletionCreateParams, kwargs)

        if max_output_tokens:
            # Newer models (o1, o3, o4, gpt-5, gpt-4.1, gpt-4o)
            # use max_completion_tokens instead of max_tokens
            if (
                model.startswith("o1")
                or model.startswith("o3")
                or model.startswith("o4")
                or model.startswith("gpt-5")
                or model.startswith("gpt-4.1")
                or model.startswith("gpt-4o")
            ):
                kwargs["max_completion_tokens"] = max_output_tokens  # type: ignore
            else:
                kwargs["max_tokens"] = max_output_tokens

        # Add reasoning_effort for o-series and GPT-5 models
        if reasoning_effort and str(model).startswith(("o1", "o3", "o4", "gpt-5")):
            kwargs["reasoning_effort"] = reasoning_effort  # type: ignore

        if functions:
            kwargs["tools"] = [  # pyright: ignore - it fails to infer the dict type
                {"type": "function", "function": format_function_def_for_openai(f)}
                for f in functions
            ]
            if len(functions) == 1:
                # force the model to call the only specified function
                kwargs["tool_choice"] = {  # pyright: ignore - type inference failure
                    "type": "function",
                    "function": {"name": functions[0].name},
                }

        if extra_headers := self._configuration.extra_request_headers:
            # 'extra_headers' is not on CompletionCreateParams, but is on chat.create()
            kwargs["extra_headers"] = kwargs.get("extra_headers", {})  # type: ignore
            kwargs["extra_headers"].update(extra_headers.copy())  # type: ignore

        prepped_messages: list[ChatCompletionMessageParam] = []
        for message in prompt_messages:
            msg_dict = message.model_dump(  # type: ignore
                include={"role", "content", "tool_calls", "tool_call_id", "name"},
                exclude_none=True,
            )
            # OpenAI requires tool_calls function arguments to be JSON strings,
            # but our internal model stores them as dicts.
            if "tool_calls" in msg_dict:
                for tc in msg_dict["tool_calls"]:
                    if "function" in tc and isinstance(
                        tc["function"].get("arguments"), dict
                    ):
                        tc["function"]["arguments"] = json.dumps(
                            tc["function"]["arguments"]
                        )
            prepped_messages.append(msg_dict)  # type: ignore[arg-type]

        if "messages" in kwargs:
            prepped_messages += kwargs["messages"]
            del kwargs["messages"]  # type: ignore - messages are added back later

        return prepped_messages, kwargs, {}