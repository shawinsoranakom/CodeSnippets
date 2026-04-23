def __init__(self, **kwargs: Unpack[OpenAIClientConfiguration]):
        if "model" not in kwargs:
            raise ValueError("model is required for OpenAIChatCompletionClient")

        model_capabilities: Optional[ModelCapabilities] = None  # type: ignore
        self._raw_config: Dict[str, Any] = dict(kwargs).copy()
        copied_args = dict(kwargs).copy()

        if "model_capabilities" in kwargs:
            model_capabilities = kwargs["model_capabilities"]
            del copied_args["model_capabilities"]

        model_info: Optional[ModelInfo] = None
        if "model_info" in kwargs:
            model_info = kwargs["model_info"]
            del copied_args["model_info"]

        add_name_prefixes: bool = False
        if "add_name_prefixes" in kwargs:
            add_name_prefixes = kwargs["add_name_prefixes"]

        include_name_in_message: bool = True
        if "include_name_in_message" in kwargs:
            include_name_in_message = kwargs["include_name_in_message"]

        # Special handling for Gemini model.
        assert "model" in copied_args and isinstance(copied_args["model"], str)
        if copied_args["model"].startswith("gemini-"):
            if "base_url" not in copied_args:
                copied_args["base_url"] = _model_info.GEMINI_OPENAI_BASE_URL
            if "api_key" not in copied_args and "GEMINI_API_KEY" in os.environ:
                copied_args["api_key"] = os.environ["GEMINI_API_KEY"]
        if copied_args["model"].startswith("claude-"):
            if "base_url" not in copied_args:
                copied_args["base_url"] = _model_info.ANTHROPIC_OPENAI_BASE_URL
            if "api_key" not in copied_args and "ANTHROPIC_API_KEY" in os.environ:
                copied_args["api_key"] = os.environ["ANTHROPIC_API_KEY"]
        if copied_args["model"].startswith("Llama-"):
            if "base_url" not in copied_args:
                copied_args["base_url"] = _model_info.LLAMA_API_BASE_URL
            if "api_key" not in copied_args and "LLAMA_API_KEY" in os.environ:
                copied_args["api_key"] = os.environ["LLAMA_API_KEY"]

        client = _openai_client_from_config(copied_args)
        create_args = _create_args_from_config(copied_args)

        super().__init__(
            client=client,
            create_args=create_args,
            model_capabilities=model_capabilities,
            model_info=model_info,
            add_name_prefixes=add_name_prefixes,
            include_name_in_message=include_name_in_message,
        )