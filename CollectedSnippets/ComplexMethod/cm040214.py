def _save_model_to_fileobj(model, fileobj, weights_format):
    config_json, metadata_json = _serialize_model_as_json(model)

    with zipfile.ZipFile(fileobj, "w") as zf:
        with zf.open(_METADATA_FILENAME, "w") as f:
            f.write(metadata_json.encode())
        with zf.open(_CONFIG_FILENAME, "w") as f:
            f.write(config_json.encode())

        weights_file_path = None
        weights_store = None
        asset_store = None
        write_zf = False
        try:
            if weights_format == "h5":
                try:
                    if is_memory_sufficient(model):
                        # Load the model weights into memory before writing
                        # .keras if the system memory is sufficient.
                        weights_store = H5IOStore(
                            _VARS_FNAME_H5, archive=zf, mode="w"
                        )
                    else:
                        # Try opening the .h5 file, then writing it to `zf` at
                        # the end of the function call. This is more memory
                        # efficient than writing the weights into memory first.
                        working_dir = pathlib.Path(fileobj.name).parent
                        weights_file_path = tempfile.NamedTemporaryFile(
                            dir=working_dir
                        )
                        weights_store = H5IOStore(
                            weights_file_path.name, mode="w"
                        )
                        write_zf = True
                except:
                    # If we can't use the local disk for any reason, write the
                    # weights into memory first, which consumes more memory.
                    weights_store = H5IOStore(
                        _VARS_FNAME_H5, archive=zf, mode="w"
                    )
            elif weights_format == "npz":
                weights_store = NpzIOStore(
                    _VARS_FNAME_NPZ, archive=zf, mode="w"
                )
            else:
                raise ValueError(
                    "Unknown `weights_format` argument. "
                    "Expected 'h5' or 'npz'. "
                    f"Received: weights_format={weights_format}"
                )

            asset_store = DiskIOStore(_ASSETS_DIRNAME, archive=zf, mode="w")

            _save_state(
                model,
                weights_store=weights_store,
                assets_store=asset_store,
                inner_path="",
                visited_saveables=set(),
            )
        except:
            # Skip the final `zf.write` if any exception is raised
            write_zf = False
            if weights_store:
                weights_store.archive = None
            raise
        finally:
            if weights_store:
                weights_store.close()
            if asset_store:
                asset_store.close()
            if write_zf and weights_file_path:
                zf.write(weights_file_path.name, _VARS_FNAME_H5)
            if weights_file_path:
                weights_file_path.close()