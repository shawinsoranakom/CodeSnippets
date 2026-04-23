def get_model_path(model_name: str) -> str:
    r"""Get the model path according to the model name."""
    user_config = load_config()
    path_dict: dict[DownloadSource, str] = SUPPORTED_MODELS.get(model_name, defaultdict(str))
    model_path = user_config["path_dict"].get(model_name, "") or path_dict.get(DownloadSource.DEFAULT, "")
    if (
        use_modelscope()
        and path_dict.get(DownloadSource.MODELSCOPE)
        and model_path == path_dict.get(DownloadSource.DEFAULT)
    ):  # replace hf path with ms path
        model_path = path_dict.get(DownloadSource.MODELSCOPE)

    if (
        use_openmind()
        and path_dict.get(DownloadSource.OPENMIND)
        and model_path == path_dict.get(DownloadSource.DEFAULT)
    ):  # replace hf path with om path
        model_path = path_dict.get(DownloadSource.OPENMIND)

    return model_path