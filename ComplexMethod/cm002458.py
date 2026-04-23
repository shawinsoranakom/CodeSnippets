def from_pretrained(
        cls,
        pretrained_model_name_or_path: str | os.PathLike,
        *init_inputs,
        cache_dir: str | os.PathLike | None = None,
        force_download: bool = False,
        local_files_only: bool = False,
        token: str | bool | None = None,
        revision: str = "main",
        trust_remote_code=False,
        **kwargs,
    ):
        r"""
        Instantiate a [`~tokenization_utils_base.PreTrainedTokenizerBase`] (or a derived class) from a predefined
        tokenizer.

        Args:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                Can be either:

                - A string, the *model id* of a predefined tokenizer hosted inside a model repo on huggingface.co.
                - A path to a *directory* containing vocabulary files required by the tokenizer, for instance saved
                  using the [`~tokenization_utils_base.PreTrainedTokenizerBase.save_pretrained`] method, e.g.,
                  `./my_model_directory/`.
                - (**Deprecated**, not applicable to all derived classes) a path to a single saved vocabulary
                  file (if and only if the tokenizer only requires a single vocabulary file like Bert or XLNet), e.g.,
                  `./my_model_directory/vocab.txt`.
            cache_dir (`str` or `os.PathLike`, *optional*):
                Path to a directory in which a downloaded predefined tokenizer vocabulary files should be cached if the
                standard cache should not be used.
            force_download (`bool`, *optional*, defaults to `False`):
                Whether or not to force the (re-)download the vocabulary files and override the cached versions if they
                exist.
            proxies (`dict[str, str]`, *optional*):
                A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
                'http://hostname': 'foo.bar:4012'}`. The proxies are used on each request.
            token (`str` or *bool*, *optional*):
                The token to use as HTTP bearer authorization for remote files. If `True`, will use the token generated
                when running `hf auth login` (stored in `~/.huggingface`).
            local_files_only (`bool`, *optional*, defaults to `False`):
                Whether or not to only rely on local files and not to attempt to download any files.
            revision (`str`, *optional*, defaults to `"main"`):
                The specific model version to use. It can be a branch name, a tag name, or a commit id, since we use a
                git-based system for storing models and other artifacts on huggingface.co, so `revision` can be any
                identifier allowed by git.
            subfolder (`str`, *optional*):
                In case the relevant files are located inside a subfolder of the model repo on huggingface.co (e.g. for
                facebook/rag-token-base), specify it here.
            inputs (additional positional arguments, *optional*):
                Will be passed along to the Tokenizer `__init__` method.
            trust_remote_code (`bool`, *optional*, defaults to `False`):
                Whether or not to allow for custom models defined on the Hub in their own modeling files. This option
                should only be set to `True` for repositories you trust and in which you have read the code, as it will
                execute code present on the Hub on your local machine.
            kwargs (additional keyword arguments, *optional*):
                Will be passed to the Tokenizer `__init__` method. Can be used to set special tokens like `bos_token`,
                `eos_token`, `unk_token`, `sep_token`, `pad_token`, `cls_token`, `mask_token`,
                `extra_special_tokens`. See parameters in the `__init__` for more details.

        <Tip>

        Passing `token=True` is required when you want to use a private model.

        </Tip>

        Examples:

        ```python
        # We can't instantiate directly the base class *PreTrainedTokenizerBase* so let's show our examples on a derived class: BertTokenizer
        # Download vocabulary from huggingface.co and cache.
        tokenizer = BertTokenizer.from_pretrained("google-bert/bert-base-uncased")

        # Download vocabulary from huggingface.co (user-uploaded) and cache.
        tokenizer = BertTokenizer.from_pretrained("dbmdz/bert-base-german-cased")

        # If vocabulary files are in a directory (e.g. tokenizer was saved using *save_pretrained('./test/saved_model/')*)
        tokenizer = BertTokenizer.from_pretrained("./test/saved_model/")

        # If the tokenizer uses a single vocabulary file, you can point directly to this file
        tokenizer = BertTokenizer.from_pretrained("./test/saved_model/my_vocab.txt")

        # You can link tokens to special vocabulary when instantiating
        tokenizer = BertTokenizer.from_pretrained("google-bert/bert-base-uncased", unk_token="<unk>")
        # You should be sure '<unk>' is in the vocabulary when doing that.
        # Otherwise use tokenizer.add_special_tokens({'unk_token': '<unk>'}) instead)
        assert tokenizer.unk_token == "<unk>"
        ```"""
        proxies = kwargs.pop("proxies", None)
        subfolder = kwargs.pop("subfolder", None)
        from_pipeline = kwargs.pop("_from_pipeline", None)
        from_auto_class = kwargs.pop("_from_auto", False)
        commit_hash = kwargs.pop("_commit_hash", None)
        gguf_file = kwargs.get("gguf_file")

        user_agent = {"file_type": "tokenizer", "from_auto_class": from_auto_class}
        if from_pipeline is not None:
            user_agent["using_pipeline"] = from_pipeline

        if is_offline_mode() and not local_files_only:
            logger.info("Offline mode: forcing local_files_only=True")
            local_files_only = True

        pretrained_model_name_or_path = str(pretrained_model_name_or_path)
        vocab_files = {}
        additional_files_names = {}
        init_configuration = {}

        is_local = os.path.isdir(pretrained_model_name_or_path)
        single_file_id = None
        if os.path.isfile(pretrained_model_name_or_path):
            # For legacy support: allow single-file loading if:
            # 1. Only one vocab file is required, OR
            # 2. It's a fast tokenizer with tokenizer_file (which is optional), OR
            # 3. It's a GGUF file
            vocab_files_count = len(cls.vocab_files_names)
            has_optional_tokenizer_file = vocab_files_count > 1 and "tokenizer_file" in cls.vocab_files_names

            if vocab_files_count > 1 and not gguf_file and not has_optional_tokenizer_file:
                raise ValueError(
                    f"Calling {cls.__name__}.from_pretrained() with the path to a single file or url is not "
                    "supported for this tokenizer. Use a model identifier or the path to a directory instead."
                )
            file_id = "vocab_file"
            if pretrained_model_name_or_path.endswith("tokenizer.json"):
                file_id = "tokenizer_file"
            vocab_files[file_id] = pretrained_model_name_or_path
            single_file_id = file_id
        else:
            if gguf_file:
                vocab_files["vocab_file"] = gguf_file
            else:
                # At this point pretrained_model_name_or_path is either a directory or a model identifier name
                additional_files_names = {
                    "added_tokens_file": ADDED_TOKENS_FILE,  # kept only for legacy
                    "special_tokens_map_file": SPECIAL_TOKENS_MAP_FILE,  # kept only for legacy
                    "tokenizer_config_file": TOKENIZER_CONFIG_FILE,
                    # tokenizer_file used to initialize a slow from a fast. Properly copy the `addedTokens` instead of adding in random orders
                    "tokenizer_file": FULL_TOKENIZER_FILE,
                    "chat_template_file": CHAT_TEMPLATE_FILE,
                }

            vocab_files = {**cls.vocab_files_names, **additional_files_names}

            # Check for versioned tokenizer files
            if "tokenizer_file" in vocab_files:
                fast_tokenizer_file = FULL_TOKENIZER_FILE
                resolved_config_file = cached_file(
                    pretrained_model_name_or_path,
                    TOKENIZER_CONFIG_FILE,
                    cache_dir=cache_dir,
                    force_download=force_download,
                    proxies=proxies,
                    token=token,
                    revision=revision,
                    local_files_only=local_files_only,
                    subfolder=subfolder,
                    user_agent=user_agent,
                    _raise_exceptions_for_missing_entries=False,
                    _commit_hash=commit_hash,
                )
                if resolved_config_file is not None:
                    with open(resolved_config_file, encoding="utf-8") as reader:
                        tokenizer_config = json.load(reader)
                        if "fast_tokenizer_files" in tokenizer_config:
                            fast_tokenizer_file = get_fast_tokenizer_file(tokenizer_config["fast_tokenizer_files"])
                    commit_hash = extract_commit_hash(resolved_config_file, commit_hash)
                vocab_files["tokenizer_file"] = fast_tokenizer_file

            # This block looks for any extra chat template files
            if is_local:
                template_dir = Path(pretrained_model_name_or_path, CHAT_TEMPLATE_DIR)
                if template_dir.is_dir():
                    for template_file in template_dir.glob("*.jinja"):
                        template_name = template_file.name.removesuffix(".jinja")
                        vocab_files[f"chat_template_{template_name}"] = f"{CHAT_TEMPLATE_DIR}/{template_file.name}"
            else:
                for template in list_repo_templates(
                    pretrained_model_name_or_path,
                    local_files_only=local_files_only,
                    revision=revision,
                    cache_dir=cache_dir,
                    token=token,
                ):
                    template = template.removesuffix(".jinja")
                    vocab_files[f"chat_template_{template}"] = f"{CHAT_TEMPLATE_DIR}/{template}.jinja"

        remote_files = []
        if not is_local and not local_files_only:
            try:
                remote_files = list_repo_files(pretrained_model_name_or_path)
            except Exception:
                remote_files = []
        elif pretrained_model_name_or_path and os.path.isdir(pretrained_model_name_or_path):
            remote_files = os.listdir(pretrained_model_name_or_path)

        if "tokenizer_file" in vocab_files and not re.search(vocab_files["tokenizer_file"], "".join(remote_files)):
            # mistral tokenizer names are different, but we can still convert them if
            # mistral common is not there
            other_pattern = r"tekken\.json|tokenizer\.model\.*|tiktoken\.model" + "|".join(
                getattr(cls, "VOCAB_FILES_NAMES", {}).keys()
            )
            if match := re.search(other_pattern, "\n".join(remote_files)):
                if "spm_file" in vocab_files:
                    vocab_files["spm_file"] = match.group()
                else:
                    vocab_files["vocab_file"] = match.group()

        resolved_vocab_files = {}
        for file_id, file_path in vocab_files.items():
            if file_path is None:
                resolved_vocab_files[file_id] = None
            elif single_file_id == file_id:
                if os.path.isfile(file_path):
                    resolved_vocab_files[file_id] = file_path
            else:
                try:
                    resolved_vocab_files[file_id] = cached_file(
                        pretrained_model_name_or_path,
                        file_path,
                        cache_dir=cache_dir,
                        force_download=force_download,
                        proxies=proxies,
                        local_files_only=local_files_only,
                        token=token,
                        user_agent=user_agent,
                        revision=revision,
                        subfolder=subfolder,
                        _raise_exceptions_for_missing_entries=False,
                        _commit_hash=commit_hash,
                    )
                except OSError:
                    # Re-raise any error raised by cached_file in order to get a helpful error message
                    raise
                except Exception:
                    # For any other exception, we throw a generic error.
                    raise OSError(
                        f"Can't load tokenizer for '{pretrained_model_name_or_path}'. If you were trying to load it from "
                        "'https://huggingface.co/models', make sure you don't have a local directory with the same name. "
                        f"Otherwise, make sure '{pretrained_model_name_or_path}' is the correct path to a directory "
                        f"containing all relevant files for a {cls.__name__} tokenizer."
                    )
                commit_hash = extract_commit_hash(resolved_vocab_files[file_id], commit_hash)

        for file_id, file_path in vocab_files.items():
            if file_id not in resolved_vocab_files:
                continue

        return cls._from_pretrained(
            resolved_vocab_files,
            pretrained_model_name_or_path,
            init_configuration,
            *init_inputs,
            token=token,
            cache_dir=cache_dir,
            local_files_only=local_files_only,
            _commit_hash=commit_hash,
            _is_local=is_local,
            trust_remote_code=trust_remote_code,
            **kwargs,
        )