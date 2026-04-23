def _load_constants(
    archive_reader: PT2ArchiveReader,
    model_name: str,
) -> dict[str, torch.Tensor] | bytes:
    # Make it BC compatible with legacy constant files
    legacy_constants_file = f"{CONSTANTS_DIR}{model_name}.pt"
    if legacy_constants_file in archive_reader.get_file_names():
        logger.warning(
            "You are loading constant from the legacy format. "
            "Please generate a new pt2 file using torch.export.save()."
        )
        return archive_reader.read_bytes(legacy_constants_file)
    else:
        constants_config_file = CONSTANTS_CONFIG_FILENAME_FORMAT.format(model_name)
        if constants_config_file not in archive_reader.get_file_names():
            raise AssertionError(f"{constants_config_file} not found in PT2 archive")
        constants_config = _load_payload_config(archive_reader, constants_config_file)
        # construct the mapping from file name (e.g. constant_0) to constant payload
        constant_file_map = _build_file_map(
            archive_reader, constants_config, CONSTANTS_DIR
        )
        # chain the mapping constant FQN -> constant file name -> strided constant payload
        # so that the aliasing of constants is preserved
        constants: dict[str, torch.Tensor] = {}
        for constant_fqn, payload_meta in constants_config.config.items():
            path_name = payload_meta.path_name
            if path_name.startswith(TENSOR_CONSTANT_FILENAME_PREFIX):
                if payload_meta.use_pickle:
                    constant_bytes = archive_reader.read_bytes(
                        os.path.join(CONSTANTS_DIR, path_name)
                    )
                    constants[constant_fqn] = torch.load(
                        io.BytesIO(constant_bytes), weights_only=False
                    )
                else:
                    tensor_meta = payload_meta.tensor_meta
                    if tensor_meta is None:
                        raise AssertionError(
                            "tensor_meta cannot be None for non-pickled constant"
                        )
                    constant_tensor = torch.as_strided(
                        input=constant_file_map[path_name],
                        size=deserialize_size(tensor_meta.sizes),
                        stride=deserialize_stride(tensor_meta.strides),
                        storage_offset=deserialize_storage_offset(
                            tensor_meta.storage_offset
                        ),
                    )
                    constants[constant_fqn] = constant_tensor

            elif path_name.startswith(CUSTOM_OBJ_FILENAME_PREFIX):
                constant_bytes = archive_reader.read_bytes(
                    os.path.join(CONSTANTS_DIR, path_name)
                )
                constants[constant_fqn] = torch._C._pickle_load_obj(constant_bytes)

            else:
                raise RuntimeError(f"Unsupported constant type: {path_name}")

        return constants