def get_video_processor_dict(
        cls, pretrained_model_name_or_path: str | os.PathLike, **kwargs
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        From a `pretrained_model_name_or_path`, resolve to a dictionary of parameters, to be used for instantiating a
        video processor of type [`~video_processing_utils.VideoProcessorBase`] using `from_dict`.

        Parameters:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                The identifier of the pre-trained checkpoint from which we want the dictionary of parameters.
            subfolder (`str`, *optional*, defaults to `""`):
                In case the relevant files are located inside a subfolder of the model repo on huggingface.co, you can
                specify the folder name here.

        Returns:
            `tuple[Dict, Dict]`: The dictionary(ies) that will be used to instantiate the video processor object.
        """
        cache_dir = kwargs.pop("cache_dir", None)
        force_download = kwargs.pop("force_download", False)
        proxies = kwargs.pop("proxies", None)
        token = kwargs.pop("token", None)
        local_files_only = kwargs.pop("local_files_only", False)
        revision = kwargs.pop("revision", None)
        subfolder = kwargs.pop("subfolder", "")

        from_pipeline = kwargs.pop("_from_pipeline", None)
        from_auto_class = kwargs.pop("_from_auto", False)

        user_agent = {"file_type": "video processor", "from_auto_class": from_auto_class}
        if from_pipeline is not None:
            user_agent["using_pipeline"] = from_pipeline

        if is_offline_mode() and not local_files_only:
            logger.info("Offline mode: forcing local_files_only=True")
            local_files_only = True

        pretrained_model_name_or_path = str(pretrained_model_name_or_path)
        is_local = os.path.isdir(pretrained_model_name_or_path)
        if os.path.isfile(pretrained_model_name_or_path):
            resolved_video_processor_file = pretrained_model_name_or_path
            resolved_processor_file = None
            is_local = True
        else:
            video_processor_file = VIDEO_PROCESSOR_NAME
            try:
                # Try to load with a new config name first and if not successful try with the old file name
                # NOTE: we save all processor configs as nested dict in PROCESSOR_NAME from v5, which is the standard
                resolved_processor_file = cached_file(
                    pretrained_model_name_or_path,
                    filename=PROCESSOR_NAME,
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
                resolved_video_processor_files = [
                    resolved_file
                    for filename in [video_processor_file, IMAGE_PROCESSOR_NAME]
                    if (
                        resolved_file := cached_file(
                            pretrained_model_name_or_path,
                            filename=filename,
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
                    )
                    is not None
                ]
                resolved_video_processor_file = (
                    resolved_video_processor_files[0] if resolved_video_processor_files else None
                )
            except OSError:
                # Raise any OS error raise by `cached_file`. It will have a helpful error message adapted to
                # the original exception.
                raise
            except Exception:
                # For any other exception, we throw a generic error.
                raise OSError(
                    f"Can't load video processor for '{pretrained_model_name_or_path}'. If you were trying to load"
                    " it from 'https://huggingface.co/models', make sure you don't have a local directory with the"
                    f" same name. Otherwise, make sure '{pretrained_model_name_or_path}' is the correct path to a"
                    f" directory containing a {video_processor_file} file"
                )

        # Load video_processor dict. Priority goes as (nested config if found -> video processor config -> image processor config)
        # We are downloading both configs because almost all models have a `processor_config.json` but
        # not all of these are nested. We need to check if it was saved recebtly as nested or if it is legacy style
        video_processor_dict = None
        if resolved_processor_file is not None:
            processor_dict = safe_load_json_file(resolved_processor_file)
            if "video_processor" in processor_dict:
                video_processor_dict = processor_dict["video_processor"]

        if resolved_video_processor_file is not None and video_processor_dict is None:
            video_processor_dict = safe_load_json_file(resolved_video_processor_file)

        if video_processor_dict is None:
            raise OSError(
                f"Can't load video processor for '{pretrained_model_name_or_path}'. If you were trying to load"
                " it from 'https://huggingface.co/models', make sure you don't have a local directory with the"
                f" same name. Otherwise, make sure '{pretrained_model_name_or_path}' is the correct path to a"
                f" directory containing a {video_processor_file} file"
            )

        if is_local:
            logger.info(f"loading configuration file {resolved_video_processor_file}")
        else:
            logger.info(
                f"loading configuration file {video_processor_file} from cache at {resolved_video_processor_file}"
            )

        return video_processor_dict, kwargs