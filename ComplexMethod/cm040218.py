def load_weights_only(
    model, filepath, skip_mismatch=False, objects_to_skip=None
):
    """Load the weights of a model from a filepath (.keras or .weights.h5).

    Note: only supports h5 for now.
    """
    if not model.built:
        raise ValueError(
            "You are loading weights into a model that has not yet been built. "
            "Try building the model first by calling it on some data or "
            "by using `build()`."
        )

    archive = None
    tmp_dir = None
    filepath_str = str(filepath)

    try:
        if file_utils.is_remote_path(filepath_str):
            tmp_dir = get_temp_dir()
            local_filepath = os.path.join(
                tmp_dir, os.path.basename(filepath_str)
            )
            file_utils.copy(filepath_str, local_filepath)
            filepath_str = filepath = local_filepath

        if filepath_str.endswith("weights.h5"):
            weights_store = H5IOStore(filepath, mode="r")
        elif filepath_str.endswith("weights.json"):
            weights_store = ShardedH5IOStore(filepath, mode="r")
        elif filepath_str.endswith(".keras"):
            archive = zipfile.ZipFile(filepath, "r")
            weights_store = H5IOStore(_VARS_FNAME_H5, archive=archive, mode="r")

        failed_saveables = set()
        if objects_to_skip is not None:
            visited_saveables = set(id(o) for o in objects_to_skip)
        else:
            visited_saveables = set()
        error_msgs = {}
        _load_state(
            model,
            weights_store=weights_store,
            assets_store=None,
            inner_path="",
            skip_mismatch=skip_mismatch,
            visited_saveables=visited_saveables,
            failed_saveables=failed_saveables,
            error_msgs=error_msgs,
        )
        weights_store.close()
        if archive:
            archive.close()

        if failed_saveables:
            _raise_loading_failure(error_msgs, warn_only=skip_mismatch)
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir)