def load_pt2(
    f: FileLike,
    *,
    expected_opset_version: dict[str, int] | None = None,
    run_single_threaded: bool = False,
    num_runners: int = 1,
    device_index: int = -1,
    load_weights_from_disk: bool = False,
) -> PT2ArchiveContents:  # type: ignore[type-arg]
    """
    Loads all the artifacts previously saved with ``package_pt2``.

    Args:
        f (str | os.PathLike[str] | IO[bytes]): A file-like object (has to
         implement write and flush) or a string containing a file name.

        expected_opset_version (Optional[Dict[str, int]]): A map of opset names
         to expected opset versions

        num_runners (int): Number of runners to load AOTInductor artifacts

        run_single_threaded (bool): Whether the model should be run without
            thread synchronization logic. This is useful to avoid conflicts with
            CUDAGraphs.

        device_index (int): The index of the device to which the PT2 package is
            to be loaded. By default, `device_index=-1` is used, which corresponds
            to the device `cuda` when using CUDA. Passing `device_index=1` would
            load the package to `cuda:1`, for example.

    Returns:
        A ``PT2ArchiveContents`` object which contains all the objects in the PT2.
    """

    from torch._inductor.cpp_builder import normalize_path_separator

    if not (
        (isinstance(f, (io.IOBase, IO)) and f.readable() and f.seekable())
        or (isinstance(f, (str, os.PathLike)) and os.fspath(f).endswith(".pt2"))
    ):
        # TODO: turn this into an error in 2.9
        logger.warning(
            "Unable to load package. f must be a buffer or a file ending in "
            ".pt2. Instead got {%s}",
            f,
        )

    if isinstance(f, (str, os.PathLike)):
        f = os.fspath(f)

    weights = {}
    weight_maps = {}
    # pyrefly: ignore [bad-argument-type]
    with PT2ArchiveReader(f) as archive_reader:
        version = archive_reader.read_string(ARCHIVE_VERSION_PATH)
        if version != ARCHIVE_VERSION_VALUE:
            raise ValueError(
                f"Saved archive version {version} does not match our current "
                f"archive version {ARCHIVE_VERSION_VALUE}."
            )

        file_names = archive_reader.get_file_names()

        exported_programs = _load_exported_programs(
            archive_reader, file_names, expected_opset_version
        )
        extra_files = _load_extra_files(archive_reader, file_names)

        # Get a list of AOTI model names
        aoti_model_names: set[str] = set()
        for file in file_names:
            if file.startswith(AOTINDUCTOR_DIR):
                file_end = file[
                    len(AOTINDUCTOR_DIR) :
                ]  # remove data/aotinductor/ prefix
                file_end = normalize_path_separator(
                    file_end
                )  # Win32 need normalize path before split.
                model_name = file_end.split("/")[
                    0
                ]  # split "model_name/...cpp" into "model_name"
                aoti_model_names.add(model_name)
                if load_weights_from_disk and file.endswith("weights_config.json"):
                    weight_map = json.loads(archive_reader.read_string(file))
                    weight_maps[model_name] = weight_map
            elif load_weights_from_disk and file.startswith(WEIGHTS_DIR):
                weight_file_name = file[
                    len(WEIGHTS_DIR) :
                ]  # remove data/weights/ prefix
                weight_bytes = archive_reader.read_bytes(file)
                loaded_weight = torch.load(io.BytesIO(weight_bytes))
                weights[weight_file_name] = loaded_weight

    if isinstance(f, (io.IOBase, IO)):
        if len(aoti_model_names) > 0:
            # Workaround for AOTIModelPackageLoader not reading buffers
            with tempfile.NamedTemporaryFile(suffix=".pt2") as tf:
                f.seek(0)
                tf.write(f.read())
                f.seek(0)
                logger.debug("Writing buffer to tmp file located at %s.", tf.name)

                aoti_runners = {
                    model_name: _load_aoti(
                        tf.name,
                        model_name,
                        run_single_threaded,
                        num_runners,
                        device_index,
                    )
                    for model_name in aoti_model_names
                }
        else:
            aoti_runners = {}
    else:
        aoti_runners = {
            model_name: _load_aoti(
                f,
                model_name,
                run_single_threaded,
                num_runners,
                device_index,
            )
            for model_name in aoti_model_names
        }

    if weight_maps:
        for model_name in aoti_model_names:
            model_weights = {}
            for weight_name, (file, shape, stride, storage_offset) in weight_maps[
                model_name
            ].items():
                weight = weights[file]
                model_weights[weight_name] = weight.as_strided(
                    shape, stride, storage_offset
                )

            # user_managed=True ensures the weights updates are shared by all runners.
            aoti_runners[model_name].load_constants(
                model_weights, check_full_update=True, user_managed=True
            )

    return PT2ArchiveContents(exported_programs, aoti_runners, extra_files)