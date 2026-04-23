def load_model(filepath, custom_objects=None, compile=True, safe_mode=True):
    """Loads a model saved via `model.save()` or from an Orbax checkpoint.

    Args:
        filepath: `str` or `pathlib.Path` object, path to the saved model file
            or Orbax checkpoint directory.
        custom_objects: Optional dictionary mapping names
            (strings) to custom classes or functions to be
            considered during deserialization.
        compile: Boolean, whether to compile the model after loading.
        safe_mode: Boolean, whether to disallow unsafe `lambda` deserialization.
            When `safe_mode=False`, loading an object has the potential to
            trigger arbitrary code execution. This argument is only
            applicable to the Keras v3 model format. Defaults to `True`.

    Returns:
        A Keras model instance. If the original model was compiled,
        and the argument `compile=True` is set, then the returned model
        will be compiled. Otherwise, the model will be left uncompiled.

    Example:

    ```python
    model = keras.Sequential([
        keras.layers.Dense(5, input_shape=(3,)),
        keras.layers.Softmax()])
    model.save("model.keras")
    loaded_model = keras.saving.load_model("model.keras")
    ```

    Note that the model variables may have different name values
    (`var.name` property, e.g. `"dense_1/kernel:0"`) after being reloaded.
    It is recommended that you use layer attributes to
    access specific variables, e.g. `model.get_layer("dense_1").kernel`.
    """
    is_keras_zip = str(filepath).endswith(".keras") and zipfile.is_zipfile(
        filepath
    )
    is_keras_dir = file_utils.isdir(filepath) and file_utils.exists(
        file_utils.join(filepath, "config.json")
    )
    is_hf = str(filepath).startswith("hf://")

    # Support for remote zip files
    if (
        file_utils.is_remote_path(filepath)
        and not file_utils.isdir(filepath)
        and not is_keras_zip
        and not is_hf
    ):
        local_path = file_utils.join(
            saving_lib.get_temp_dir(), os.path.basename(filepath)
        )

        # Copy from remote to temporary local directory
        file_utils.copy(filepath, local_path)

        # Switch filepath to local zipfile for loading model
        if zipfile.is_zipfile(local_path):
            filepath = local_path
            is_keras_zip = True

    if is_keras_zip or is_keras_dir or is_hf:
        return saving_lib.load_model(
            filepath,
            custom_objects=custom_objects,
            compile=compile,
            safe_mode=safe_mode,
        )
    if str(filepath).endswith((".h5", ".hdf5")):
        return legacy_h5_format.load_model_from_hdf5(
            filepath,
            custom_objects=custom_objects,
            compile=compile,
            safe_mode=safe_mode,
        )

    # Check for Orbax checkpoint directory using utility function
    if is_orbax_checkpoint(filepath):
        return _load_model_from_orbax_checkpoint(
            filepath,
            custom_objects=custom_objects,
            compile=compile,
            safe_mode=safe_mode,
        )

    elif str(filepath).endswith(".keras"):
        raise ValueError(
            f"File not found: filepath={filepath}. "
            "Please ensure the file is an accessible `.keras` "
            "zip file."
        )
    else:
        raise ValueError(
            f"File format not supported: filepath={filepath}. "
            "Keras 3 only supports V3 `.keras` files, "
            "legacy H5 format files (`.h5` extension). "
            "Note that the legacy SavedModel format is not "
            "supported by `load_model()` in Keras 3. In "
            "order to reload a TensorFlow SavedModel as an "
            "inference-only layer in Keras 3, use "
            "`keras.layers.TFSMLayer("
            f"{filepath}, call_endpoint='serving_default')` "
            "(note that your `call_endpoint` "
            "might have a different name)."
        )