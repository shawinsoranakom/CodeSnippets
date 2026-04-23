def save_weights_only(
    model, filepath, max_shard_size=None, objects_to_skip=None
):
    """Save only the weights of a model to a target filepath.

    Supports both `.weights.h5` and `.keras`.
    """
    if not model.built:
        raise ValueError(
            "You are saving a model that has not yet been built. "
            "Try building the model first by calling it on some data or "
            "by using `build()`."
        )

    filepath_str = str(filepath)
    tmp_dir = None
    remote_filepath = None
    if max_shard_size is None and not filepath_str.endswith(".weights.h5"):
        raise ValueError(
            "The filename must end in `.weights.h5`. "
            f"Received: filepath={filepath_str}"
        )
    elif max_shard_size is not None and not filepath_str.endswith(
        ("weights.h5", "weights.json")
    ):
        raise ValueError(
            "The filename must end in `.weights.json` when `max_shard_size` is "
            f"specified. Received: filepath={filepath_str}"
        )
    try:
        if file_utils.is_remote_path(filepath):
            tmp_dir = get_temp_dir()
            local_filepath = os.path.join(tmp_dir, os.path.basename(filepath))
            remote_filepath = filepath
            filepath = local_filepath

        if max_shard_size is not None:
            weights_store = ShardedH5IOStore(filepath, max_shard_size, mode="w")
        else:
            weights_store = H5IOStore(filepath, mode="w")
        if objects_to_skip is not None:
            visited_saveables = set(id(o) for o in objects_to_skip)
        else:
            visited_saveables = set()
        _save_state(
            model,
            weights_store=weights_store,
            assets_store=None,
            inner_path="",
            visited_saveables=visited_saveables,
        )
        weights_store.close()
    finally:
        if tmp_dir is not None:
            file_utils.copy(filepath, remote_filepath)
            shutil.rmtree(tmp_dir)