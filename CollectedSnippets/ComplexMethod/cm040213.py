def save_model(model, filepath, weights_format="h5", zipped=True):
    """Save a zip-archive representing a Keras model to the given file or path.

    The zip-based archive contains the following structure:

    - JSON-based configuration file (config.json): Records of model, layer, and
        other saveables' configuration.
    - H5-based saveable state files, found in respective directories, such as
        model/states.npz, model/dense_layer/states.npz, etc.
    - Metadata file.

    The states of Keras saveables (layers, optimizers, loss, and metrics) are
    automatically saved as long as they can be discovered through the attributes
    returned by `dir(Model)`. Typically, the state includes the variables
    associated with the saveable, but some specially purposed layers may
    contain more such as the vocabularies stored in the hashmaps. The saveables
    define how their states are saved by exposing `save_state()` and
    `load_state()` APIs.

    For the case of layer states, the variables will be visited as long as
    they are either 1) referenced via layer attributes, or 2) referenced via a
    container (list, tuple, or dict), and the container is referenced via a
    layer attribute.
    """
    if weights_format == "h5" and h5py is None:
        raise ImportError("h5py must be installed in order to save a model.")

    if not model.built:
        warnings.warn(
            "You are saving a model that has not yet been built. "
            "It might not contain any weights yet. "
            "Consider building the model first by calling it "
            "on some data.",
            stacklevel=2,
        )

    if isinstance(filepath, io.IOBase):
        _save_model_to_fileobj(model, filepath, weights_format)
        return

    filepath = str(filepath)
    is_hf = filepath.startswith("hf://")
    if zipped and not filepath.endswith(".keras"):
        raise ValueError(
            "Invalid `filepath` argument: expected a `.keras` extension. "
            f"Received: filepath={filepath}"
        )
    if not zipped and filepath.endswith(".keras"):
        raise ValueError(
            "When using `zipped=False`, the `filepath` argument should not "
            f"end in `.keras`. Received: filepath={filepath}"
        )
    if zipped and is_hf:
        raise ValueError(
            "When saving to the Hugging Face Hub, you should not save the "
            f"model as zipped. Received: filepath={filepath}, zipped={zipped}"
        )
    if is_hf:
        _upload_model_to_hf(model, filepath, weights_format)
    elif not zipped:
        _save_model_to_dir(model, filepath, weights_format)
    else:
        if file_utils.is_remote_path(filepath):
            # Remote path. Zip to local memory byte io and copy to remote
            zip_filepath = io.BytesIO()
            _save_model_to_fileobj(model, zip_filepath, weights_format)
            with file_utils.File(filepath, "wb") as f:
                f.write(zip_filepath.getvalue())
        else:
            with open(filepath, "wb") as f:
                _save_model_to_fileobj(model, f, weights_format)