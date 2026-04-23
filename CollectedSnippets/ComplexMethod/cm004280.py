def from_pretrained(
        cls, pretrained_model_name_or_path, *inputs, **kwargs
    ) -> TokenizersBackend | SentencePieceBackend:
        r"""
        Instantiate one of the tokenizer classes of the library from a pretrained model vocabulary.

        The tokenizer class to instantiate is selected based on the `model_type` property of the config object (either
        passed as an argument or loaded from `pretrained_model_name_or_path` if possible), or when it's missing, by
        falling back to using pattern matching on `pretrained_model_name_or_path`:

        List options

        Params:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                Can be either:

                    - A string, the *model id* of a predefined tokenizer hosted inside a model repo on huggingface.co.
                    - A path to a *directory* containing vocabulary files required by the tokenizer, for instance saved
                      using the [`~PreTrainedTokenizer.save_pretrained`] method, e.g., `./my_model_directory/`.
                    - a path to a single saved vocabulary file if and only if the tokenizer only requires a
                      single vocabulary file (like Bert or XLNet), e.g.: `./my_model_directory/vocab.txt`. (Not
                      applicable to all derived classes)
            inputs (additional positional arguments, *optional*):
                Will be passed along to the Tokenizer `__init__()` method.
            config ([`PreTrainedConfig`], *optional*)
                The configuration object used to determine the tokenizer class to instantiate.
            cache_dir (`str` or `os.PathLike`, *optional*):
                Path to a directory in which a downloaded pretrained model configuration should be cached if the
                standard cache should not be used.
            force_download (`bool`, *optional*, defaults to `False`):
                Whether or not to force the (re-)download the model weights and configuration files and override the
                cached versions if they exist.
            proxies (`dict[str, str]`, *optional*):
                A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
                'http://hostname': 'foo.bar:4012'}`. The proxies are used on each request.
            revision (`str`, *optional*, defaults to `"main"`):
                The specific model version to use. It can be a branch name, a tag name, or a commit id, since we use a
                git-based system for storing models and other artifacts on huggingface.co, so `revision` can be any
                identifier allowed by git.
            subfolder (`str`, *optional*):
                In case the relevant files are located inside a subfolder of the model repo on huggingface.co (e.g. for
                facebook/rag-token-base), specify it here.
            tokenizer_type (`str`, *optional*):
                Tokenizer type to be loaded.
            backend (`str`, *optional*, defaults to `"tokenizers"`):
                Backend to use for tokenization. Valid options are:
                - `"tokenizers"`: Use the HuggingFace tokenizers library backend (default)
                - `"sentencepiece"`: Use the SentencePiece backend
            trust_remote_code (`bool`, *optional*, defaults to `False`):
                Whether or not to allow for custom models defined on the Hub in their own modeling files. This option
                should only be set to `True` for repositories you trust and in which you have read the code, as it will
                execute code present on the Hub on your local machine.
            kwargs (additional keyword arguments, *optional*):
                Will be passed to the Tokenizer `__init__()` method. Can be used to set special tokens like
                `bos_token`, `eos_token`, `unk_token`, `sep_token`, `pad_token`, `cls_token`, `mask_token`,
                `additional_special_tokens`. See parameters in the `__init__()` for more details.

        Examples:

        ```python
        >>> from transformers import AutoTokenizer

        >>> # Download vocabulary from huggingface.co and cache.
        >>> tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")

        >>> # Download vocabulary from huggingface.co (user-uploaded) and cache.
        >>> tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-german-cased")

        >>> # If vocabulary files are in a directory (e.g. tokenizer was saved using *save_pretrained('./test/saved_model/')*)
        >>> # tokenizer = AutoTokenizer.from_pretrained("./test/bert_saved_model/")

        >>> # Download vocabulary from huggingface.co and define model-specific arguments
        >>> tokenizer = AutoTokenizer.from_pretrained("FacebookAI/roberta-base", add_prefix_space=True)

        >>> # Explicitly use the tokenizers backend
        >>> tokenizer = AutoTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer", backend="tokenizers")

        >>> # Explicitly use the sentencepiece backend
        >>> tokenizer = AutoTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer", backend="sentencepiece")
        ```"""
        config = kwargs.pop("config", None)
        kwargs["_from_auto"] = True

        # V5: Always use fast tokenizers, ignore use_fast parameter
        _ = kwargs.pop("use_fast", None)
        tokenizer_type = kwargs.pop("tokenizer_type", None)
        trust_remote_code = kwargs.pop("trust_remote_code", None)
        gguf_file = kwargs.get("gguf_file")

        # First, let's see whether the tokenizer_type is passed so that we can leverage it
        if tokenizer_type is not None:
            tokenizer_class_name = TOKENIZER_MAPPING_NAMES.get(tokenizer_type, None)

            if tokenizer_class_name is None:
                raise ValueError(
                    f"Passed `tokenizer_type` {tokenizer_type} does not exist. `tokenizer_type` should be one of "
                    f"{', '.join(c for c in TOKENIZER_MAPPING_NAMES)}."
                )

            tokenizer_class = tokenizer_class_from_name(tokenizer_class_name)

            if tokenizer_class is None:
                raise ValueError(f"Tokenizer class {tokenizer_class_name} is not currently imported.")

            return tokenizer_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)

        if gguf_file:
            gguf_path = cached_file(pretrained_model_name_or_path, gguf_file, **kwargs)
            config_dict = load_gguf_checkpoint(gguf_path, return_tensors=False)["config"]
            config = AutoConfig.for_model(**config_dict)
        elif config is None:
            try:
                config = AutoConfig.from_pretrained(
                    pretrained_model_name_or_path, trust_remote_code=trust_remote_code, **kwargs
                )
            except (ValueError, OSError):
                config = PreTrainedConfig.from_pretrained(pretrained_model_name_or_path, **kwargs)

        config_model_type = config.model_type

        # Next, let's try to use the tokenizer_config file to get the tokenizer class.
        tokenizer_config = get_tokenizer_config(pretrained_model_name_or_path, **kwargs)
        tokenizer_config_class = tokenizer_config.get("tokenizer_class", None)

        # Check for auto_map early to handle dynamic tokenizers properly
        tokenizer_auto_map = None
        if "auto_map" in tokenizer_config:
            if isinstance(tokenizer_config["auto_map"], (tuple, list)):
                # Legacy format for dynamic tokenizers
                tokenizer_auto_map = tokenizer_config["auto_map"]
            else:
                tokenizer_auto_map = tokenizer_config["auto_map"].get("AutoTokenizer", None)

        # if there is a config, we can check that the tokenizer class != than model class.
        # Use the config class if it's a specialized tokenizer, otherwise fall back to TokenizersBackend.
        if (
            tokenizer_auto_map is None
            and tokenizer_config_class is not None
            and config_model_type is not None
            and config_model_type != ""
            and TOKENIZER_MAPPING_NAMES.get(config_model_type) is not None
            and (TOKENIZER_MAPPING_NAMES.get(config_model_type).removesuffix("Fast"))
            != (tokenizer_config_class.removesuffix("Fast"))
        ):
            tokenizer_class = tokenizer_class_from_name(tokenizer_config_class)
            if tokenizer_class is not None and tokenizer_class.__name__ not in (
                "TokenizersBackend",
                "PythonBackend",
                "PreTrainedTokenizerFast",
            ):
                return tokenizer_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)

            if TokenizersBackend is not None:
                return TokenizersBackend.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)

            raise ValueError(
                f"Tokenizer class '{tokenizer_config_class}' specified in the tokenizer config was not found. "
                f"The tokenizer may need to be converted or re-saved."
            )

        if "_commit_hash" in tokenizer_config:
            kwargs["_commit_hash"] = tokenizer_config["_commit_hash"]

        if tokenizer_config_class and tokenizer_config_class.endswith("Fast"):
            tokenizer_config_class = tokenizer_config_class[:-4]

        has_remote_code = tokenizer_auto_map is not None
        has_local_code = type(config) in TOKENIZER_MAPPING or (
            tokenizer_config_class is not None
            and (
                tokenizer_class_from_name(tokenizer_config_class) is not None
                or tokenizer_class_from_name(tokenizer_config_class + "Fast") is not None
            )
        )
        explicit_local_code = (
            has_local_code
            and type(config) not in TOKENIZER_MAPPING
            and (
                tokenizer_config_class is not None
                and not (
                    tokenizer_class_from_name(tokenizer_config_class)
                    or tokenizer_class_from_name(tokenizer_config_class + "Fast")
                ).__module__.startswith("transformers.")
            )
        )
        # V5: Skip remote tokenizer for custom models with incorrect hub tokenizer class
        if has_remote_code and config_model_type in MODELS_WITH_INCORRECT_HUB_TOKENIZER_CLASS:
            has_remote_code = False
            tokenizer_auto_map = None

        if has_remote_code:
            # V5: Always prefer fast tokenizer (index 1), fallback to slow (index 0)
            if tokenizer_auto_map[1] is not None:
                class_ref = tokenizer_auto_map[1]
            else:
                class_ref = tokenizer_auto_map[0]
            if "--" in class_ref:
                upstream_repo = class_ref.split("--")[0]
            else:
                upstream_repo = None
            trust_remote_code = resolve_trust_remote_code(
                trust_remote_code, pretrained_model_name_or_path, has_local_code, has_remote_code, upstream_repo
            )

        if has_remote_code and trust_remote_code and not explicit_local_code:
            # BC v5: register *Fast aliases before remote code loads.
            if tokenizer_config_class:
                tokenizer_class_from_name(tokenizer_config_class.removesuffix("Fast"))
            tokenizer_class = get_class_from_dynamic_module(class_ref, pretrained_model_name_or_path, **kwargs)
            _ = kwargs.pop("code_revision", None)
            tokenizer_class.register_for_auto_class()
            return tokenizer_class.from_pretrained(
                pretrained_model_name_or_path, *inputs, trust_remote_code=trust_remote_code, **kwargs
            )
        elif tokenizer_config_class is not None:
            tokenizer_class_candidate = tokenizer_config_class
            tokenizer_class = tokenizer_class_from_name(tokenizer_class_candidate)
            if tokenizer_class is None and not tokenizer_class_candidate.endswith("Fast"):
                tokenizer_class = tokenizer_class_from_name(tokenizer_class_candidate + "Fast")
            if tokenizer_class is not None and tokenizer_class.__name__ == "PythonBackend":
                tokenizer_class = TokenizersBackend
            # Fallback to TokenizersBackend if the class wasn't found
            if tokenizer_class is None:
                tokenizer_class = TokenizersBackend

            return tokenizer_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)
        elif getattr(config, "tokenizer_class", None):
            _class = config.tokenizer_class
            if "PreTrainedTokenizerFast" not in _class and _class.endswith("Fast"):
                _class = _class[:-4]
            tokenizer_class = tokenizer_class_from_name(_class)
            return tokenizer_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)

        # Otherwise we have to be creative.
        # if model is an encoder decoder, the encoder tokenizer class is used by default
        if isinstance(config, EncoderDecoderConfig):
            if type(config.decoder) is not type(config.encoder):
                logger.warning(
                    f"The encoder model config class: {config.encoder.__class__} is different from the decoder model "
                    f"config class: {config.decoder.__class__}. It is not recommended to use the "
                    "`AutoTokenizer.from_pretrained()` method in this case. Please use the encoder and decoder "
                    "specific tokenizer classes."
                )
            config = config.encoder

        model_type = config_class_to_model_type(type(config).__name__) or getattr(config, "model_type", None)
        if model_type is not None:
            tokenizer_class = TOKENIZER_MAPPING.get(type(config), TokenizersBackend)
            if tokenizer_class is not None:
                return tokenizer_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)

        # Fallback: try tokenizer_class from tokenizer_config.json
        tokenizer_config_class = tokenizer_config.get("tokenizer_class", None)
        if tokenizer_config_class is not None:
            if tokenizer_config_class != "TokenizersBackend" and tokenizer_config_class.endswith("Fast"):
                tokenizer_config_class = tokenizer_config_class[:-4]
            tokenizer_class = tokenizer_class_from_name(tokenizer_config_class)
            if tokenizer_class is None and not tokenizer_config_class.endswith("Fast"):
                tokenizer_class = tokenizer_class_from_name(tokenizer_config_class + "Fast")
            if tokenizer_class is not None and tokenizer_class.__name__ == "PythonBackend":
                tokenizer_class = TokenizersBackend
            if tokenizer_class is None:
                tokenizer_class = TokenizersBackend
            return tokenizer_class.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)

        raise ValueError(
            f"Unrecognized configuration class {config.__class__} to build an AutoTokenizer.\n"
            f"Model type should be one of {', '.join(c.__name__ for c in TOKENIZER_MAPPING)}."
        )