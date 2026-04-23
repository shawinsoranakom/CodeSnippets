def __init__(
        self,
        client: Union[AsyncOpenAI, AsyncAzureOpenAI],
        *,
        create_args: Dict[str, Any],
        model_capabilities: Optional[ModelCapabilities] = None,  # type: ignore
        model_info: Optional[ModelInfo] = None,
        add_name_prefixes: bool = False,
        include_name_in_message: bool = True,
    ):
        self._client = client
        self._add_name_prefixes = add_name_prefixes
        self._include_name_in_message = include_name_in_message
        if model_capabilities is None and model_info is None:
            try:
                self._model_info = _model_info.get_info(create_args["model"])
            except KeyError as err:
                raise ValueError("model_info is required when model name is not a valid OpenAI model") from err
        elif model_capabilities is not None and model_info is not None:
            raise ValueError("model_capabilities and model_info are mutually exclusive")
        elif model_capabilities is not None and model_info is None:
            warnings.warn(
                "model_capabilities is deprecated, use model_info instead",
                DeprecationWarning,
                stacklevel=2,
            )
            info = cast(ModelInfo, model_capabilities)
            info["family"] = ModelFamily.UNKNOWN
            self._model_info = info
        elif model_capabilities is None and model_info is not None:
            self._model_info = model_info

        # Validate model_info, check if all required fields are present
        validate_model_info(self._model_info)

        self._resolved_model: Optional[str] = None
        if "model" in create_args:
            self._resolved_model = _model_info.resolve_model(create_args["model"])

        if (
            not self._model_info["json_output"]
            and "response_format" in create_args
            and (
                isinstance(create_args["response_format"], dict)
                and create_args["response_format"]["type"] == "json_object"
            )
        ):
            raise ValueError("Model does not support JSON output.")

        self._create_args = create_args
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        self._actual_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)