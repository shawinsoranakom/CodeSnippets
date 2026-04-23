def save_model_to_hdf5(model, filepath, overwrite=True, include_optimizer=True):
    if h5py is None:
        raise ImportError(
            "`save_model()` using h5 format requires h5py. Could not "
            "import h5py."
        )

    if not isinstance(filepath, h5py.File):
        # If file exists and should not be overwritten.
        if not overwrite and os.path.isfile(filepath):
            proceed = io_utils.ask_to_proceed_with_overwrite(filepath)
            if not proceed:
                return

        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        f = h5py.File(filepath, mode="w")
        opened_new_file = True
    else:
        f = filepath
        opened_new_file = False
    try:
        with saving_options.keras_option_scope(use_legacy_config=True):
            model_metadata = saving_utils.model_metadata(
                model, include_optimizer
            )
            for k, v in model_metadata.items():
                if isinstance(v, (dict, list, tuple)):
                    f.attrs[k] = json.dumps(
                        v, default=json_utils.get_json_type
                    ).encode("utf8")
                else:
                    f.attrs[k] = v

            model_weights_group = f.create_group("model_weights")
            save_weights_to_hdf5_group(model_weights_group, model)

            # TODO(b/128683857): Add integration tests between tf.keras and
            # external Keras, to avoid breaking TF.js users.
            if include_optimizer and hasattr(model, "optimizer"):
                save_optimizer_weights_to_hdf5_group(f, model.optimizer)

        f.flush()
    finally:
        if opened_new_file:
            f.close()