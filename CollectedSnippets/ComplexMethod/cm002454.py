def __init__(self, **kwargs):
        self.init_inputs = ()
        for key in kwargs:
            if hasattr(self, key) and callable(getattr(self, key)):
                raise AttributeError(f"{key} conflicts with the method {key} in {self.__class__.__name__}")

        # V5: Convert deprecated additional_special_tokens to extra_special_tokens before storing init_kwargs
        if "additional_special_tokens" in kwargs and "extra_special_tokens" not in kwargs:
            kwargs["extra_special_tokens"] = kwargs.pop("additional_special_tokens")

        self.init_kwargs = copy.deepcopy(kwargs)
        self.name_or_path = kwargs.pop("name_or_path", "")
        self._processor_class = kwargs.pop("processor_class", None)

        self._pad_token_type_id = 0
        self.verbose = kwargs.pop("verbose", False)

        # V5: Separate storage for named special tokens and extra special tokens
        self._special_tokens_map = dict.fromkeys(self.SPECIAL_TOKENS_ATTRIBUTES)
        self._extra_special_tokens = []  # List of extra model-specific special tokens

        # V5: track both explicit and auto-detected model-specific tokens
        explicit_model_specific_tokens = kwargs.pop("model_specific_special_tokens", None)
        if explicit_model_specific_tokens is None:
            explicit_model_specific_tokens = {}
        elif not isinstance(explicit_model_specific_tokens, dict):
            raise TypeError("model_specific_special_tokens must be a dictionary of token name to token value")
        auto_model_specific_tokens = {}

        # Directly set hidden values to allow init with tokens not yet in vocab
        for key in list(kwargs.keys()):
            if key in self.SPECIAL_TOKENS_ATTRIBUTES:
                value = kwargs.pop(key)
                if value is None:
                    continue
                if isinstance(value, (str, AddedToken)):
                    self._special_tokens_map[key] = value
                else:
                    raise TypeError(f"Special token {key} has to be either str or AddedToken but got: {type(value)}")
            elif key == "extra_special_tokens":
                value = kwargs.pop(key)
                if value is None:
                    continue
                if isinstance(value, dict):
                    self._set_model_specific_special_tokens(special_tokens=value)
                elif isinstance(value, (list, tuple)):
                    self._extra_special_tokens = list(value)
                else:
                    raise TypeError("extra_special_tokens must be a list/tuple of tokens or a dict of named tokens")
            elif (
                key.endswith("_token")
                and key not in self.SPECIAL_TOKENS_ATTRIBUTES
                and isinstance(kwargs[key], (str, AddedToken))
            ):
                value = kwargs.pop(key)
                if value is None:
                    continue
                auto_model_specific_tokens[key] = value

        # For backward compatibility we fallback to set model_max_length from max_len if provided
        model_max_length = kwargs.pop("model_max_length", kwargs.pop("max_len", None))
        self.model_max_length = model_max_length if model_max_length is not None else VERY_LARGE_INTEGER

        self.padding_side = kwargs.pop("padding_side", self.padding_side)
        if self.padding_side not in ["right", "left"]:
            raise ValueError(
                f"Padding side should be selected between 'right' and 'left', current value: {self.padding_side}"
            )

        self.truncation_side = kwargs.pop("truncation_side", self.truncation_side)
        if self.truncation_side not in ["right", "left"]:
            raise ValueError(
                f"Truncation side should be selected between 'right' and 'left', current value: {self.truncation_side}"
            )

        self.model_input_names = kwargs.pop("model_input_names", self.model_input_names)

        # By default, clean up tokenization spaces for both fast and slow tokenizers
        self.clean_up_tokenization_spaces = kwargs.pop("clean_up_tokenization_spaces", False)

        # By default, do not split special tokens for both fast and slow tokenizers
        self.split_special_tokens = kwargs.pop("split_special_tokens", False)

        self._in_target_context_manager = False

        self.chat_template = kwargs.pop("chat_template", None)
        if isinstance(self.chat_template, (list, tuple)):
            # Chat templates are stored as lists of dicts with fixed key names,
            # we reconstruct that into a single dict while loading them.
            self.chat_template = {template["name"]: template["template"] for template in self.chat_template}

        self.response_schema = kwargs.pop("response_schema", None)

        model_specific_tokens = {**auto_model_specific_tokens, **explicit_model_specific_tokens}
        if model_specific_tokens:
            self._set_model_specific_special_tokens(special_tokens=model_specific_tokens)

        self.deprecation_warnings = {}

        # Backend information (V5: tracking which backend and files were used)
        self.backend = kwargs.pop("backend", None)
        self.files_loaded = kwargs.pop("files_loaded", [])