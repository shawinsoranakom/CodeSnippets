def load_weights(model, filepath, skip_mismatch=False, **kwargs):
    filepath_str = str(filepath)

    # Get the legacy kwargs.
    objects_to_skip = kwargs.pop("objects_to_skip", None)
    by_name = kwargs.pop("by_name", None)
    if kwargs:
        raise ValueError(f"Invalid keyword arguments: {kwargs}")

    if filepath_str.endswith(".keras"):
        if objects_to_skip is not None:
            raise ValueError(
                "`objects_to_skip` only supports loading '.weights.h5' files."
                f"Received: {filepath}"
            )
        if by_name is not None:
            raise ValueError(
                "`by_name` only supports loading legacy '.h5' or '.hdf5' "
                f"files. Received: {filepath}"
            )

        saving_lib.load_weights_only(
            model, filepath, skip_mismatch=skip_mismatch
        )
    elif filepath_str.endswith(".weights.h5") or filepath_str.endswith(
        ".weights.json"
    ):
        if by_name is not None:
            raise ValueError(
                "`by_name` only supports loading legacy '.h5' or '.hdf5' "
                f"files. Received: {filepath}"
            )
        saving_lib.load_weights_only(
            model,
            filepath,
            skip_mismatch=skip_mismatch,
            objects_to_skip=objects_to_skip,
        )
    elif filepath_str.endswith(".h5") or filepath_str.endswith(".hdf5"):
        if objects_to_skip is not None:
            raise ValueError(
                "`objects_to_skip` only supports loading '.weights.h5' files."
                f"Received: {filepath}"
            )
        if not h5py.available:
            raise ImportError(
                "Loading HDF5 files requires the h5py package. "
                "You can install it via `pip install h5py`"
            )
        with h5py.File(filepath, "r") as f:
            if "layer_names" not in f.attrs and "model_weights" in f:
                f = f["model_weights"]
            if by_name:
                legacy_h5_format.load_weights_from_hdf5_group_by_name(
                    f, model, skip_mismatch
                )
            else:
                legacy_h5_format.load_weights_from_hdf5_group(
                    f, model, skip_mismatch
                )
    elif is_orbax_checkpoint(filepath):
        # Load weights from Orbax checkpoint
        filepath = str(filepath)

        # Determine if this is a root directory or a step directory
        items = file_utils.listdir(filepath)
        has_step_subdirs = any(
            file_utils.isdir(file_utils.join(filepath, item)) and item.isdigit()
            for item in items
        )

        if has_step_subdirs:
            # It's a root directory, find the latest checkpoint
            checkpoint_path = find_latest_orbax_checkpoint(filepath)
        else:
            # It's a step directory, use it directly
            checkpoint_path = filepath

        # Build abstract pytree with target shardings so Orbax can
        # reshard arrays onto the current distribution layout.
        abstract_pytree = build_orbax_abstract_pytree(
            checkpoint_path, model.get_state_tree()
        )

        loaded_checkpointables = ocp.load_checkpointables(
            checkpoint_path, dict(pytree=abstract_pytree)
        )

        loaded_state = loaded_checkpointables["pytree"]

        # Set the model state directly from the loaded state
        model.set_state_tree(loaded_state)
    else:
        raise ValueError(
            f"File format not supported: filepath={filepath}. "
            "Keras 3 only supports V3 `.keras` files, "
            "`.weights.h5` files, legacy H5 format files "
            "(`.h5` extension), or Orbax checkpoints."
        )