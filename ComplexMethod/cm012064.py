def _get_torch_related_args(
    include_pytorch: bool, aot_mode: bool
) -> tuple[list[str], list[str], list[str]]:
    from torch.utils.cpp_extension import include_paths, TORCH_LIB_PATH

    libraries = []
    include_dirs = include_paths()

    if config.aot_inductor.link_libtorch:
        libraries_dirs = [TORCH_LIB_PATH]
        if sys.platform != "darwin" and not config.is_fbcode():
            libraries.extend(["torch", "torch_cpu"])
            if _IS_WINDOWS:
                libraries.append("c10")
            if not aot_mode:
                libraries.append("torch_python")
    else:
        libraries_dirs = []
        if config.aot_inductor.cross_target_platform == "windows":
            aoti_shim_library = config.aot_inductor.aoti_shim_library

            assert aoti_shim_library, (
                "'config.aot_inductor.aoti_shim_library' must be set when 'cross_target_platform' is 'windows'."
            )
            if isinstance(aoti_shim_library, str):
                libraries.append(aoti_shim_library)
            else:
                assert isinstance(aoti_shim_library, list)
                libraries.extend(aoti_shim_library)

    if config.aot_inductor.cross_target_platform == "windows":
        assert config.aot_inductor.aoti_shim_library_path, (
            "'config.aot_inductor.aoti_shim_library_path' must be set to the path of the AOTI shim library",
            " when 'cross_target_platform' is 'windows'.",
        )
        libraries_dirs.append(config.aot_inductor.aoti_shim_library_path)

    if _IS_WINDOWS:
        libraries.append("sleef")

    return include_dirs, libraries_dirs, libraries