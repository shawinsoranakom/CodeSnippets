def _package_aoti_files(
    archive_writer: PT2ArchiveWriter,
    aoti_files: AOTI_FILES | None,
    pickle_protocol: int = DEFAULT_PICKLE_PROTOCOL,
) -> None:
    if aoti_files is None:
        return

    if isinstance(aoti_files, list):
        aoti_files = {"model": aoti_files}

    if not isinstance(aoti_files, dict):
        raise AssertionError(
            f"Expected aoti_files to be a dict, but got {type(aoti_files)}"
        )

    all_weights: dict[str, Weights] = {}  # model_name -> weight
    weights_configs: dict[
        str, dict[str, Any]
    ] = {}  # model_name -> (weight_name -> (filename, shape, stride, offset))

    for model_name, files in aoti_files.items():
        num_so_files = 0
        weights_configs[model_name] = {}

        for file in files:
            if file == "":
                continue

            if isinstance(file, Weights):
                all_weights[model_name] = file
                continue

            if file.endswith(".so"):
                num_so_files += 1
                if num_so_files > 1:
                    raise RuntimeError(
                        f"Multiple .so files found in {files}. "
                        "You might need to clear your cache "
                        "directory before calling aoti_compile again."
                    )

            filename = os.path.basename(file)
            if filename.startswith(CUSTOM_OBJ_FILENAME_PREFIX):
                new_filepath = os.path.join(CONSTANTS_DIR, filename)
            else:
                new_filepath = os.path.join(AOTINDUCTOR_DIR, model_name, filename)
            logger.debug(
                "Saving AOTI generated file %s to archive in %s", file, new_filepath
            )
            archive_writer.write_file(
                str(new_filepath),
                file,
            )

    if len(all_weights) > 0:
        # Dedup weights
        grouped_tensors: list[OrderedSet[tuple[str, str]]] = group_weights(all_weights)
        for idx, group in enumerate(grouped_tensors):
            filename = f"{WEIGHT_FILENAME_PREFIX}{idx}"
            complete_tensor = get_complete_tensor(group, all_weights)
            buffer = io.BytesIO()
            torch.save(complete_tensor, buffer, pickle_protocol=pickle_protocol)
            archive_writer.write_bytes(
                os.path.join(WEIGHTS_DIR, filename), buffer.getvalue()
            )
            for model_name, weight_name in group:
                _, w_property = all_weights[model_name].get_weight(weight_name)
                weights_configs[model_name][weight_name] = (
                    filename,
                    w_property.shape,
                    w_property.stride,
                    w_property.offset,
                )

        for model_name, weights_config in weights_configs.items():
            archive_writer.write_string(
                os.path.join(AOTINDUCTOR_DIR, model_name, "weights_config.json"),
                json.dumps(weights_config),
            )
            logger.debug("packaging weights_config for model %s", model_name)
            logger.debug(weights_config)