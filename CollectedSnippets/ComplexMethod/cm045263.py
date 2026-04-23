def __init__(
        self,
        model_info: Optional[ModelInfo] = None,
        **kwargs: Unpack[LlamaCppParams],
    ) -> None:
        """
        Initialize the LlamaCpp client.
        """

        if model_info:
            validate_model_info(model_info)
            self._model_info = model_info
        else:
            # Default model info.
            self._model_info = self.DEFAULT_MODEL_INFO

        if "repo_id" in kwargs and "filename" in kwargs and kwargs["repo_id"] and kwargs["filename"]:
            repo_id: str = cast(str, kwargs.pop("repo_id"))
            filename: str = cast(str, kwargs.pop("filename"))
            pretrained = Llama.from_pretrained(repo_id=repo_id, filename=filename, **kwargs)  # type: ignore
            assert isinstance(pretrained, Llama)
            self.llm = pretrained

        elif "model_path" in kwargs:
            self.llm = Llama(**kwargs)  # pyright: ignore[reportUnknownMemberType]
        else:
            raise ValueError("Please provide model_path if ... or provide repo_id and filename if ....")
        self._total_usage = {"prompt_tokens": 0, "completion_tokens": 0}