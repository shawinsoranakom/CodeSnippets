def _rocm_include_paths(dst_file_ext: str) -> list[str]:
    from torch.utils import cpp_extension

    rocm_include = (
        os.path.join(config.rocm.rocm_home, "include")
        if config.rocm.rocm_home
        else cpp_extension._join_rocm_home("include")
    )

    if config.is_fbcode():
        from libfb.py import parutil

        ck_path = parutil.get_dir_path("composable-kernel-headers")
    else:
        if not config.rocm.ck_dir:
            ck_dir, _, _, _ = try_import_ck_lib()
            if not ck_dir:
                log.warning("Unspecified Composable Kernel directory")
            config.rocm.ck_dir = ck_dir
        ck_path = config.rocm.ck_dir or cpp_extension._join_rocm_home(
            "composable_kernel"
        )

    log.debug("Using ck path %s", ck_path)

    ck_include = os.path.join(ck_path, "include")
    ck_library_include = os.path.join(ck_path, "library", "include")

    # CK has to take priority over ROCm include paths
    # Since CK is potentially more up-to-date
    paths = [
        os.path.realpath(p) for p in (ck_include, ck_library_include, rocm_include)
    ]
    if dst_file_ext == "exe":
        ck_utility_include = os.path.join(ck_path, "library", "src", "utility")
        paths.append(os.path.realpath(ck_utility_include))
    return paths