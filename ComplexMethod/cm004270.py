def from_pretrained(cls, pretrained_model_name_or_path: str | os.PathLike[str], *model_args, **kwargs):
        config = kwargs.pop("config", None)
        trust_remote_code = kwargs.get("trust_remote_code")
        kwargs["_from_auto"] = True
        hub_kwargs_names = [
            "cache_dir",
            "force_download",
            "local_files_only",
            "proxies",
            "revision",
            "subfolder",
            "token",
        ]
        hub_kwargs = {name: kwargs.pop(name) for name in hub_kwargs_names if name in kwargs}
        code_revision = kwargs.pop("code_revision", None)
        commit_hash = kwargs.pop("_commit_hash", None)
        adapter_kwargs = kwargs.pop("adapter_kwargs", None)

        token = hub_kwargs.pop("token", None)

        if token is not None:
            hub_kwargs["token"] = token

        if commit_hash is None:
            if not isinstance(config, PreTrainedConfig):
                # We make a call to the config file first (which may be absent) to get the commit hash as soon as possible
                resolved_config_file = cached_file(
                    pretrained_model_name_or_path,
                    CONFIG_NAME,
                    _raise_exceptions_for_gated_repo=False,
                    _raise_exceptions_for_missing_entries=False,
                    _raise_exceptions_for_connection_errors=False,
                    **hub_kwargs,
                )
                commit_hash = extract_commit_hash(resolved_config_file, commit_hash)
            else:
                commit_hash = getattr(config, "_commit_hash", None)

        if is_peft_available():
            if adapter_kwargs is None:
                adapter_kwargs = {}
            adapter_kwargs = adapter_kwargs.copy()  # avoid mutating original
            if token is not None:
                adapter_kwargs["token"] = token

            maybe_adapter_path = find_adapter_config_file(
                pretrained_model_name_or_path, _commit_hash=commit_hash, **adapter_kwargs
            )

            if maybe_adapter_path is not None:
                with open(maybe_adapter_path, "r", encoding="utf-8") as f:
                    adapter_config = json.load(f)

                    adapter_kwargs["_adapter_model_path"] = pretrained_model_name_or_path
                    # Only override the model name/path if the current value doesn't point to a
                    # complete model with an embedded adapter so that local models with embedded
                    # adapters will load from the local base model rather than pull the base
                    # model named in the adapter's config from the hub.
                    if not os.path.exists(pretrained_model_name_or_path) or not os.path.exists(
                        os.path.join(pretrained_model_name_or_path, CONFIG_NAME)
                    ):
                        pretrained_model_name_or_path = adapter_config["base_model_name_or_path"]

        if not isinstance(config, PreTrainedConfig):
            kwargs_orig = copy.deepcopy(kwargs)
            # ensure not to pollute the config object with dtype="auto" - since it's
            # meaningless in the context of the config object - torch.dtype values are acceptable
            if kwargs.get("torch_dtype") == "auto":
                _ = kwargs.pop("torch_dtype")
            if kwargs.get("dtype") == "auto":
                _ = kwargs.pop("dtype")
            # to not overwrite the quantization_config if config has a quantization_config
            if kwargs.get("quantization_config") is not None:
                _ = kwargs.pop("quantization_config")

            config, kwargs = AutoConfig.from_pretrained(
                pretrained_model_name_or_path,
                return_unused_kwargs=True,
                code_revision=code_revision,
                _commit_hash=commit_hash,
                **hub_kwargs,
                **kwargs,
            )

            # if torch_dtype=auto was passed here, ensure to pass it on
            if kwargs_orig.get("torch_dtype", None) == "auto":
                kwargs["torch_dtype"] = "auto"
            if kwargs_orig.get("dtype", None) == "auto":
                kwargs["dtype"] = "auto"
            if kwargs_orig.get("quantization_config", None) is not None:
                kwargs["quantization_config"] = kwargs_orig["quantization_config"]

        has_remote_code = hasattr(config, "auto_map") and cls.__name__ in config.auto_map
        has_local_code = type(config) in cls._model_mapping
        explicit_local_code = has_local_code and not _get_model_class(
            config, cls._model_mapping
        ).__module__.startswith("transformers.")
        upstream_repo = None
        if has_remote_code:
            class_ref = config.auto_map[cls.__name__]
            if "--" in class_ref:
                upstream_repo = class_ref.split("--")[0]
        trust_remote_code = resolve_trust_remote_code(
            trust_remote_code,
            pretrained_model_name_or_path,
            has_local_code,
            has_remote_code,
            upstream_repo=upstream_repo,
        )
        kwargs["trust_remote_code"] = trust_remote_code

        # Set the adapter kwargs
        kwargs["adapter_kwargs"] = adapter_kwargs

        if has_remote_code and trust_remote_code and not explicit_local_code:
            model_class = get_class_from_dynamic_module(
                class_ref, pretrained_model_name_or_path, code_revision=code_revision, **hub_kwargs, **kwargs
            )
            _ = hub_kwargs.pop("code_revision", None)
            # This block handles the case where the user is loading a model with `trust_remote_code=True`
            # but a library model exists with the same name. We don't want to override the autoclass
            # mappings in this case, or all future loads of that model will be the remote code model.
            if not has_local_code:
                cls.register(config.__class__, model_class, exist_ok=True)
                model_class.register_for_auto_class(auto_class=cls)
            model_class = add_generation_mixin_to_remote_model(model_class)
            return model_class.from_pretrained(
                pretrained_model_name_or_path, *model_args, config=config, **hub_kwargs, **kwargs
            )
        elif has_local_code:
            model_class = _get_model_class(config, cls._model_mapping)
            if model_class.config_class == config.sub_configs.get("text_config", None):
                # TODO: Validate that copying the parent quantization config to the text sub-config preserves
                # modules_to_not_convert and skip-module matching when composite-model module prefixes differ.
                parent_config = config
                config = config.get_text_config()
                # Propagate quantization_config from the composite parent config so that
                # `get_hf_quantizer` can correctly detect the model as pre-quantized.
                if hasattr(parent_config, "quantization_config"):
                    config.quantization_config = parent_config.quantization_config
            return model_class.from_pretrained(
                pretrained_model_name_or_path, *model_args, config=config, **hub_kwargs, **kwargs
            )
        raise ValueError(
            f"Unrecognized configuration class {config.__class__} for this kind of AutoModel: {cls.__name__}.\n"
            f"Model type should be one of {', '.join(c.__name__ for c in cls._model_mapping)}."
        )