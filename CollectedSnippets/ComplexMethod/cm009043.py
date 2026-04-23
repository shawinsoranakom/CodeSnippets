def __init__(
        self,
        model: str | BaseChatModel,
        *,
        trigger: ContextSize | list[ContextSize] | None = None,
        keep: ContextSize = ("messages", _DEFAULT_MESSAGES_TO_KEEP),
        token_counter: TokenCounter = count_tokens_approximately,
        summary_prompt: str = DEFAULT_SUMMARY_PROMPT,
        trim_tokens_to_summarize: int | None = _DEFAULT_TRIM_TOKEN_LIMIT,
        **deprecated_kwargs: Any,
    ) -> None:
        """Initialize summarization middleware.

        Args:
            model: The language model to use for generating summaries.
            trigger: One or more thresholds that trigger summarization.

                Provide a single
                [`ContextSize`][langchain.agents.middleware.summarization.ContextSize]
                tuple or a list of tuples, in which case summarization runs when any
                threshold is met.

                !!! example

                    ```python
                    # Trigger summarization when 50 messages is reached
                    ("messages", 50)

                    # Trigger summarization when 3000 tokens is reached
                    ("tokens", 3000)

                    # Trigger summarization either when 80% of model's max input tokens
                    # is reached or when 100 messages is reached (whichever comes first)
                    [("fraction", 0.8), ("messages", 100)]
                    ```

                    See [`ContextSize`][langchain.agents.middleware.summarization.ContextSize]
                    for more details.
            keep: Context retention policy applied after summarization.

                Provide a [`ContextSize`][langchain.agents.middleware.summarization.ContextSize]
                tuple to specify how much history to preserve.

                Defaults to keeping the most recent `20` messages.

                Does not support multiple values like `trigger`.

                !!! example

                    ```python
                    # Keep the most recent 20 messages
                    ("messages", 20)

                    # Keep the most recent 3000 tokens
                    ("tokens", 3000)

                    # Keep the most recent 30% of the model's max input tokens
                    ("fraction", 0.3)
                    ```
            token_counter: Function to count tokens in messages.
            summary_prompt: Prompt template for generating summaries.
            trim_tokens_to_summarize: Maximum tokens to keep when preparing messages for
                the summarization call.

                Pass `None` to skip trimming entirely.
        """
        # Handle deprecated parameters
        if "max_tokens_before_summary" in deprecated_kwargs:
            value = deprecated_kwargs["max_tokens_before_summary"]
            warnings.warn(
                "max_tokens_before_summary is deprecated. Use trigger=('tokens', value) instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if trigger is None and value is not None:
                trigger = ("tokens", value)

        if "messages_to_keep" in deprecated_kwargs:
            value = deprecated_kwargs["messages_to_keep"]
            warnings.warn(
                "messages_to_keep is deprecated. Use keep=('messages', value) instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if keep == ("messages", _DEFAULT_MESSAGES_TO_KEEP):
                keep = ("messages", value)

        super().__init__()

        if isinstance(model, str):
            model = init_chat_model(model)

        self.model = model
        if trigger is None:
            self.trigger: ContextSize | list[ContextSize] | None = None
            trigger_conditions: list[ContextSize] = []
        elif isinstance(trigger, list):
            validated_list = [self._validate_context_size(item, "trigger") for item in trigger]
            self.trigger = validated_list
            trigger_conditions = validated_list
        else:
            validated = self._validate_context_size(trigger, "trigger")
            self.trigger = validated
            trigger_conditions = [validated]
        self._trigger_conditions = trigger_conditions

        self.keep = self._validate_context_size(keep, "keep")
        if token_counter is count_tokens_approximately:
            self.token_counter = _get_approximate_token_counter(self.model)
            self._partial_token_counter: TokenCounter = partial(  # type: ignore[call-arg]
                self.token_counter, use_usage_metadata_scaling=False
            )
        else:
            self.token_counter = token_counter
            self._partial_token_counter = token_counter
        self.summary_prompt = summary_prompt
        self.trim_tokens_to_summarize = trim_tokens_to_summarize

        requires_profile = any(condition[0] == "fraction" for condition in self._trigger_conditions)
        if self.keep[0] == "fraction":
            requires_profile = True
        if requires_profile and self._get_profile_limits() is None:
            msg = (
                "Model profile information is required to use fractional token limits, "
                "and is unavailable for the specified model. Please use absolute token "
                "counts instead, or pass "
                '`\n\nChatModel(..., profile={"max_input_tokens": ...})`.\n\n'
                "with a desired integer value of the model's maximum input tokens."
            )
            raise ValueError(msg)