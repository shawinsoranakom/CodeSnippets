def __init__(
        self,
        name: str,
        code_executor: CodeExecutor,
        *,
        model_client: ChatCompletionClient | None = None,
        model_context: ChatCompletionContext | None = None,
        model_client_stream: bool = False,
        max_retries_on_error: int = 0,
        description: str | None = None,
        system_message: str | None = DEFAULT_SYSTEM_MESSAGE,
        sources: Sequence[str] | None = None,
        supported_languages: List[str] | None = None,
        approval_func: Optional[ApprovalFuncType] = None,
    ) -> None:
        if description is None:
            if model_client is None:
                description = CodeExecutorAgent.DEFAULT_TERMINAL_DESCRIPTION
            else:
                description = CodeExecutorAgent.DEFAULT_AGENT_DESCRIPTION

        super().__init__(name=name, description=description)
        self._code_executor = code_executor
        self._sources = sources
        self._model_client_stream = model_client_stream
        self._max_retries_on_error = max_retries_on_error
        self._approval_func = approval_func
        self._approval_func_is_async = approval_func is not None and iscoroutinefunction(approval_func)

        # Issue warning if no approval function is set
        if approval_func is None:
            import warnings

            warnings.warn(
                "No approval function set for CodeExecutorAgent. This means code will be executed automatically without human oversight. "
                "For security, consider setting an approval_func to review and approve code before execution. "
                "See the CodeExecutorAgent documentation for examples of approval functions.",
                UserWarning,
                stacklevel=2,
            )

        if supported_languages is not None:
            self._supported_languages = supported_languages
        else:
            self._supported_languages = CodeExecutorAgent.DEFAULT_SUPPORTED_LANGUAGES

        self._supported_languages_regex = "|".join(re.escape(lang) for lang in self._supported_languages)

        self._model_client = None
        if model_client is not None:
            self._model_client = model_client

        if model_context is not None:
            self._model_context = model_context
        else:
            self._model_context = UnboundedChatCompletionContext()

        self._system_messaages: List[SystemMessage] = []
        if system_message is None:
            self._system_messages = []
        else:
            self._system_messages = [SystemMessage(content=system_message)]

        if self._max_retries_on_error > 0:
            if not self._model_client or not self._model_client.model_info:
                raise ValueError("model_client.model_info must be provided when max_retries_on_error > 0")
            if not self._model_client.model_info["structured_output"]:
                raise ValueError("Specified model_client doesn't support structured output mode.")