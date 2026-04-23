def _get_config_dict(
        cls, pretrained_model_name_or_path: str | os.PathLike, **kwargs
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        cache_dir = kwargs.pop("cache_dir", None)
        force_download = kwargs.pop("force_download", False)
        proxies = kwargs.pop("proxies", None)
        token = kwargs.pop("token", None)
        local_files_only = kwargs.pop("local_files_only", False)
        revision = kwargs.pop("revision", None)
        trust_remote_code = kwargs.pop("trust_remote_code", None)
        subfolder = kwargs.pop("subfolder", "")
        from_pipeline = kwargs.pop("_from_pipeline", None)
        from_auto_class = kwargs.pop("_from_auto", False)
        commit_hash = kwargs.pop("_commit_hash", None)

        gguf_file = kwargs.get("gguf_file")

        if trust_remote_code is True:
            logger.warning(
                "The argument `trust_remote_code` is to be used with Auto classes. It has no effect here and is"
                " ignored."
            )

        user_agent = {"file_type": "config", "from_auto_class": from_auto_class}
        if from_pipeline is not None:
            user_agent["using_pipeline"] = from_pipeline

        pretrained_model_name_or_path = str(pretrained_model_name_or_path)

        is_local = os.path.isdir(pretrained_model_name_or_path)
        if os.path.isfile(os.path.join(subfolder, pretrained_model_name_or_path)):
            # Special case when pretrained_model_name_or_path is a local file
            resolved_config_file = pretrained_model_name_or_path
            is_local = True
        else:
            configuration_file = kwargs.pop("_configuration_file", CONFIG_NAME) if gguf_file is None else gguf_file

            try:
                # Load from local folder or from cache or download from model Hub and cache
                resolved_config_file = cached_file(
                    pretrained_model_name_or_path,
                    configuration_file,
                    cache_dir=cache_dir,
                    force_download=force_download,
                    proxies=proxies,
                    local_files_only=local_files_only,
                    token=token,
                    user_agent=user_agent,
                    revision=revision,
                    subfolder=subfolder,
                    _commit_hash=commit_hash,
                )
                if resolved_config_file is None:
                    return None, kwargs
                commit_hash = extract_commit_hash(resolved_config_file, commit_hash)
            except OSError:
                # Raise any environment error raise by `cached_file`. It will have a helpful error message adapted to
                # the original exception.
                raise
            except Exception:
                # For any other exception, we throw a generic error.
                raise OSError(
                    f"Can't load the configuration of '{pretrained_model_name_or_path}'. If you were trying to load it"
                    " from 'https://huggingface.co/models', make sure you don't have a local directory with the same"
                    f" name. Otherwise, make sure '{pretrained_model_name_or_path}' is the correct path to a directory"
                    f" containing a {configuration_file} file"
                )

        try:
            if gguf_file:
                config_dict = load_gguf_checkpoint(resolved_config_file, return_tensors=False)["config"]
            else:
                # Load config dict
                config_dict = cls._dict_from_json_file(resolved_config_file)

            config_dict["_commit_hash"] = commit_hash
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise OSError(f"It looks like the config file at '{resolved_config_file}' is not a valid JSON file.")

        if is_local:
            logger.info(f"loading configuration file {resolved_config_file}")
        else:
            logger.info(f"loading configuration file {configuration_file} from cache at {resolved_config_file}")

        # timm models are not saved with the model_type in the config file
        if "model_type" not in config_dict and is_timm_config_dict(config_dict):
            config_dict["model_type"] = "timm_wrapper"

        # Some checkpoints may contain the wrong model_type in the config file.
        # Allow the user to override it but warn them that it might not work.
        if "model_type" in kwargs and config_dict["model_type"] != kwargs["model_type"]:
            logger.warning(
                f"{configuration_file} has 'model_type={config_dict['model_type']}' but you overrode "
                f"it with 'model_type={kwargs['model_type']}'. This may lead to unexpected behavior."
            )
            config_dict["model_type"] = kwargs["model_type"]

        return config_dict, kwargs