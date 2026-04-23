def _save_state(
    saveable,
    weights_store,
    assets_store,
    inner_path,
    visited_saveables,
):
    from keras.src.saving.keras_saveable import KerasSaveable

    if not isinstance(
        weights_store, (H5IOStore, ShardedH5IOStore, NpzIOStore, type(None))
    ):
        raise ValueError(
            "Expected `weights_store` to be an instance of "
            "`H5IOStore`, `ShardedH5IOStore`, `NpzIOStore`, or `None`. "
            f"Received: {weights_store} of type {type(weights_store)}"
        )
    if not isinstance(assets_store, (DiskIOStore, type(None))):
        raise ValueError(
            "Expected `assets_store` to be an instance of "
            "`DiskIOStore` or `None`. "
            f"Received: {assets_store} of type {type(assets_store)}"
        )

    # If the saveable has already been saved, skip it.
    if id(saveable) in visited_saveables:
        return

    if hasattr(saveable, "save_own_variables") and weights_store:
        if hasattr(saveable, "name") and isinstance(saveable.name, str):
            metadata = {"name": saveable.name}
        else:
            metadata = None
        saveable.save_own_variables(
            weights_store.make(inner_path, metadata=metadata)
        )
    if hasattr(saveable, "save_assets") and assets_store:
        saveable.save_assets(assets_store.make(inner_path))

    visited_saveables.add(id(saveable))

    # Recursively save state of children saveables (layers, optimizers, etc.)
    for child_attr, child_obj in _walk_saveable(saveable):
        if isinstance(child_obj, KerasSaveable):
            _save_state(
                child_obj,
                weights_store,
                assets_store,
                inner_path=file_utils.join(inner_path, child_attr).replace(
                    "\\", "/"
                ),
                visited_saveables=visited_saveables,
            )
        elif isinstance(child_obj, (list, dict, tuple, set)):
            _save_container_state(
                child_obj,
                weights_store,
                assets_store,
                inner_path=file_utils.join(inner_path, child_attr).replace(
                    "\\", "/"
                ),
                visited_saveables=visited_saveables,
            )