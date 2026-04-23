def get_processor_dict(
        cls, pretrained_model_name_or_path: str | os.PathLike, **kwargs
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        From a `pretrained_model_name_or_path`, resolve to a dictionary of parameters, to be used for instantiating a
        processor of type [`~processing_utils.ProcessingMixin`] using `from_args_and_dict`.

        Parameters:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                The identifier of the pre-trained checkpoint from which we want the dictionary of parameters.
            subfolder (`str`, *optional*, defaults to `""`):
                In case the relevant files are located inside a subfolder of the model repo on huggingface.co, you can
                specify the folder name here.

        Returns:
            `tuple[Dict, Dict]`: The dictionary(ies) that will be used to instantiate the processor object.
        """
        # holding a copy for optionally loading the audio tokenizer (if available)
        audio_tokenizer_kwargs = copy.deepcopy(kwargs)

        cache_dir = kwargs.pop("cache_dir", None)
        force_download = kwargs.pop("force_download", False)
        proxies = kwargs.pop("proxies", None)
        token = kwargs.pop("token", None)
        local_files_only = kwargs.pop("local_files_only", False)
        revision = kwargs.pop("revision", None)
        subfolder = kwargs.pop("subfolder", "")

        from_pipeline = kwargs.pop("_from_pipeline", None)
        from_auto_class = kwargs.pop("_from_auto", False)

        user_agent = {"file_type": "processor", "from_auto_class": from_auto_class}
        if from_pipeline is not None:
            user_agent["using_pipeline"] = from_pipeline

        if is_offline_mode() and not local_files_only:
            logger.info("Offline mode: forcing local_files_only=True")
            local_files_only = True

        pretrained_model_name_or_path = str(pretrained_model_name_or_path)
        is_local = os.path.isdir(pretrained_model_name_or_path)
        if os.path.isdir(pretrained_model_name_or_path):
            processor_file = os.path.join(pretrained_model_name_or_path, PROCESSOR_NAME)

        additional_chat_template_files = {}
        resolved_additional_chat_template_files = {}
        if os.path.isfile(pretrained_model_name_or_path):
            resolved_processor_file = pretrained_model_name_or_path
            # can't load chat-template and audio tokenizer when given a file as pretrained_model_name_or_path
            resolved_chat_template_file = None
            resolved_raw_chat_template_file = None
            resolved_audio_tokenizer_file = None
            is_local = True
        else:
            if is_local:
                template_dir = Path(pretrained_model_name_or_path, CHAT_TEMPLATE_DIR)
                if template_dir.is_dir():
                    for template_file in template_dir.glob("*.jinja"):
                        template_name = template_file.stem
                        additional_chat_template_files[template_name] = f"{CHAT_TEMPLATE_DIR}/{template_file.name}"
            else:
                try:
                    for template in list_repo_templates(
                        pretrained_model_name_or_path,
                        local_files_only=local_files_only,
                        revision=revision,
                        cache_dir=cache_dir,
                        token=token,
                    ):
                        template = template.removesuffix(".jinja")
                        additional_chat_template_files[template] = f"{CHAT_TEMPLATE_DIR}/{template}.jinja"
                except EntryNotFoundError:
                    pass  # No template dir means no template files
            processor_file = PROCESSOR_NAME

            try:
                # Load from local folder or from cache or download from model Hub and cache
                resolved_processor_file = cached_file(
                    pretrained_model_name_or_path,
                    processor_file,
                    cache_dir=cache_dir,
                    force_download=force_download,
                    proxies=proxies,
                    local_files_only=local_files_only,
                    token=token,
                    user_agent=user_agent,
                    revision=revision,
                    subfolder=subfolder,
                    _raise_exceptions_for_missing_entries=False,
                )

                # chat_template.json is a legacy file used by the processor class
                # a raw chat_template.jinja is preferred in future
                resolved_chat_template_file = cached_file(
                    pretrained_model_name_or_path,
                    LEGACY_PROCESSOR_CHAT_TEMPLATE_FILE,
                    cache_dir=cache_dir,
                    force_download=force_download,
                    proxies=proxies,
                    local_files_only=local_files_only,
                    token=token,
                    user_agent=user_agent,
                    revision=revision,
                    subfolder=subfolder,
                    _raise_exceptions_for_missing_entries=False,
                )

                resolved_raw_chat_template_file = cached_file(
                    pretrained_model_name_or_path,
                    CHAT_TEMPLATE_FILE,
                    cache_dir=cache_dir,
                    force_download=force_download,
                    proxies=proxies,
                    local_files_only=local_files_only,
                    token=token,
                    user_agent=user_agent,
                    revision=revision,
                    subfolder=subfolder,
                    _raise_exceptions_for_missing_entries=False,
                )

                resolved_additional_chat_template_files = {
                    template_name: cached_file(
                        pretrained_model_name_or_path,
                        template_file,
                        cache_dir=cache_dir,
                        force_download=force_download,
                        proxies=proxies,
                        local_files_only=local_files_only,
                        token=token,
                        user_agent=user_agent,
                        revision=revision,
                        subfolder=subfolder,
                        _raise_exceptions_for_missing_entries=False,
                    )
                    for template_name, template_file in additional_chat_template_files.items()
                }

                resolved_audio_tokenizer_file = cached_file(
                    pretrained_model_name_or_path,
                    AUDIO_TOKENIZER_NAME,
                    cache_dir=cache_dir,
                    force_download=force_download,
                    proxies=proxies,
                    local_files_only=local_files_only,
                    token=token,
                    user_agent=user_agent,
                    revision=revision,
                    subfolder=subfolder,
                    _raise_exceptions_for_missing_entries=False,
                )
            except OSError:
                # Raise any environment error raise by `cached_file`. It will have a helpful error message adapted to
                # the original exception.
                raise
            except Exception:
                # For any other exception, we throw a generic error.
                raise OSError(
                    f"Can't load processor for '{pretrained_model_name_or_path}'. If you were trying to load"
                    " it from 'https://huggingface.co/models', make sure you don't have a local directory with the"
                    f" same name. Otherwise, make sure '{pretrained_model_name_or_path}' is the correct path to a"
                    f" directory containing a {PROCESSOR_NAME} file"
                )

        # Add chat template as kwarg before returning because most models don't have processor config
        if resolved_chat_template_file is not None:
            # This is the legacy path
            with open(resolved_chat_template_file, encoding="utf-8") as reader:
                chat_template_json = json.loads(reader.read())
                chat_templates = {"default": chat_template_json["chat_template"]}
                if resolved_additional_chat_template_files:
                    raise ValueError(
                        "Cannot load chat template due to conflicting files - this checkpoint combines "
                        "a legacy chat_template.json file with separate template files, which is not "
                        "supported. To resolve this error, replace the legacy chat_template.json file "
                        "with a modern chat_template.jinja file."
                    )
        else:
            chat_templates = {
                template_name: open(template_file, "r", encoding="utf-8").read()
                for template_name, template_file in resolved_additional_chat_template_files.items()
            }
            if resolved_raw_chat_template_file is not None:
                with open(resolved_raw_chat_template_file, "r", encoding="utf-8") as reader:
                    chat_templates["default"] = reader.read()
        if isinstance(chat_templates, dict) and "default" in chat_templates and len(chat_templates) == 1:
            chat_templates = chat_templates["default"]  # Flatten when we just have a single template/file

        # Existing processors on the Hub created before #27761 being merged don't have `processor_config.json` (if not
        # updated afterward), and we need to keep `from_pretrained` work. So here it fallbacks to the empty dict.
        # (`cached_file` called using `_raise_exceptions_for_missing_entries=False` to avoid exception)
        # However, for models added in the future, we won't get the expected error if this file is missing.
        if resolved_processor_file is None:
            # In any case we need to pass `chat_template` if it is available
            processor_dict = {}
        else:
            try:
                # Load processor dict
                with open(resolved_processor_file, encoding="utf-8") as reader:
                    text = reader.read()
                processor_dict = json.loads(text)

            except json.JSONDecodeError:
                raise OSError(
                    f"It looks like the config file at '{resolved_processor_file}' is not a valid JSON file."
                )

        if is_local:
            logger.info(f"loading configuration file {resolved_processor_file}")
        else:
            logger.info(f"loading configuration file {processor_file} from cache at {resolved_processor_file}")

        if processor_dict.get("chat_template") is not None:
            logger.warning_once(
                "Chat templates should be in a 'chat_template.jinja' file but found key='chat_template' "
                "in the processor's config. Make sure to move your template to its own file."
            )
        elif chat_templates:
            processor_dict["chat_template"] = chat_templates

        # Audio tokenizer needs to load the model checkpoint first, because the saved
        # json file contains only references to the model path and repo id
        if resolved_audio_tokenizer_file is not None or "audio_tokenizer" in processor_dict:
            if resolved_audio_tokenizer_file is not None:
                reader = open(resolved_audio_tokenizer_file, "r", encoding="utf-8")
                audio_tokenizer_dict = reader.read()
                audio_tokenizer_dict = json.loads(audio_tokenizer_dict)
            else:
                audio_tokenizer_dict = processor_dict["audio_tokenizer"]

            audio_tokenizer_class = cls.get_possibly_dynamic_module(audio_tokenizer_dict["audio_tokenizer_class"])
            audio_tokenizer_path = audio_tokenizer_dict["audio_tokenizer_name_or_path"]
            processor_dict["audio_tokenizer"] = audio_tokenizer_class.from_pretrained(
                audio_tokenizer_path, **audio_tokenizer_kwargs
            )

        return processor_dict, kwargs