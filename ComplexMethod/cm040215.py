def _load_model_from_dir(dirpath, custom_objects, compile, safe_mode):
    if not file_utils.exists(dirpath):
        raise ValueError(f"Directory doesn't exist: {dirpath}")
    if not file_utils.isdir(dirpath):
        raise ValueError(f"Path isn't a directory: {dirpath}")

    with open(file_utils.join(dirpath, _CONFIG_FILENAME), "r") as f:
        config_json = f.read()
    model = _model_from_config(config_json, custom_objects, compile, safe_mode)

    all_filenames = file_utils.listdir(dirpath)
    try:
        if _VARS_FNAME_H5 in all_filenames:
            weights_file_path = file_utils.join(dirpath, _VARS_FNAME_H5)
            weights_store = H5IOStore(weights_file_path, mode="r")
        elif _VARS_FNAME_NPZ in all_filenames:
            weights_file_path = file_utils.join(dirpath, _VARS_FNAME_NPZ)
            weights_store = NpzIOStore(weights_file_path, mode="r")
        else:
            raise ValueError(
                f"Expected a {_VARS_FNAME_H5} or {_VARS_FNAME_NPZ} file."
            )
        if len(all_filenames) > 3:
            asset_store = DiskIOStore(
                file_utils.join(dirpath, _ASSETS_DIRNAME), mode="r"
            )

        else:
            asset_store = None

        failed_saveables = set()
        error_msgs = {}
        _load_state(
            model,
            weights_store=weights_store,
            assets_store=asset_store,
            inner_path="",
            visited_saveables=set(),
            failed_saveables=failed_saveables,
            error_msgs=error_msgs,
        )

    finally:
        weights_store.close()
        if asset_store:
            asset_store.close()

    if failed_saveables:
        _raise_loading_failure(error_msgs)
    return model