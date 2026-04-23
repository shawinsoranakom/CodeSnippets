def _load_model_from_fileobj(fileobj, custom_objects, compile, safe_mode):
    with zipfile.ZipFile(fileobj, "r") as zf:
        with zf.open(_CONFIG_FILENAME, "r") as f:
            config_json = f.read()

        model = _model_from_config(
            config_json, custom_objects, compile, safe_mode
        )

        all_filenames = zf.namelist()
        extract_dir = None
        weights_store = None
        asset_store = None
        try:
            if _VARS_FNAME_H5 in all_filenames:
                try:
                    if is_memory_sufficient(model):
                        # Load the entire file into memory if the system memory
                        # is sufficient.
                        io_file = io.BytesIO(
                            zf.open(_VARS_FNAME_H5, "r").read()
                        )
                        weights_store = H5IOStore(io_file, mode="r")
                    else:
                        # Try extracting the model.weights.h5 file, and then
                        # loading it using using h5py. This is significantly
                        # faster than reading from the zip archive on the fly.
                        extract_dir = tempfile.TemporaryDirectory(
                            dir=pathlib.Path(fileobj.name).parent
                        )
                        zf.extract(_VARS_FNAME_H5, extract_dir.name)
                        weights_store = H5IOStore(
                            pathlib.Path(extract_dir.name, _VARS_FNAME_H5),
                            mode="r",
                        )
                except:
                    # If we can't use the local disk for any reason, read the
                    # weights from the zip archive on the fly, which is less
                    # efficient.
                    weights_store = H5IOStore(_VARS_FNAME_H5, zf, mode="r")
            elif _VARS_FNAME_NPZ in all_filenames:
                weights_store = NpzIOStore(_VARS_FNAME_NPZ, zf, mode="r")
            else:
                raise ValueError(
                    f"Expected a {_VARS_FNAME_H5} or {_VARS_FNAME_NPZ} file."
                )

            if len(all_filenames) > 3:
                asset_store = DiskIOStore(_ASSETS_DIRNAME, archive=zf, mode="r")

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
            if weights_store:
                weights_store.close()
            if asset_store:
                asset_store.close()
            if extract_dir:
                extract_dir.cleanup()

        if failed_saveables:
            _raise_loading_failure(error_msgs)
    return model