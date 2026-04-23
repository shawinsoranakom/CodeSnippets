def save_weights(
    model, filepath, overwrite=True, max_shard_size=None, **kwargs
):
    filepath_str = str(filepath)
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
        exists = os.path.exists(filepath)
    except TypeError:
        exists = False
    if exists and not overwrite:
        proceed = io_utils.ask_to_proceed_with_overwrite(filepath_str)
        if not proceed:
            return
    saving_lib.save_weights_only(model, filepath, max_shard_size, **kwargs)