def try_download_model_from_other_hub(model_args: "ModelArguments") -> str:
    if (not use_modelscope() and not use_openmind()) or os.path.exists(model_args.model_name_or_path):
        return model_args.model_name_or_path

    if use_modelscope():
        check_version("modelscope>=1.14.0", mandatory=True)
        from modelscope import snapshot_download  # type: ignore
        from modelscope.hub.api import HubApi  # type: ignore

        if model_args.ms_hub_token:
            api = HubApi()
            api.login(model_args.ms_hub_token)

        revision = "master" if model_args.model_revision == "main" else model_args.model_revision
        with WeakFileLock(os.path.abspath(os.path.expanduser("~/.cache/llamafactory/modelscope.lock"))):
            model_path = snapshot_download(
                model_args.model_name_or_path,
                revision=revision,
                cache_dir=model_args.cache_dir,
            )

        return model_path

    if use_openmind():
        check_version("openmind>=0.8.0", mandatory=True)
        from openmind.utils.hub import snapshot_download  # type: ignore

        with WeakFileLock(os.path.abspath(os.path.expanduser("~/.cache/llamafactory/openmind.lock"))):
            model_path = snapshot_download(
                model_args.model_name_or_path,
                revision=model_args.model_revision,
                cache_dir=model_args.cache_dir,
            )

        return model_path