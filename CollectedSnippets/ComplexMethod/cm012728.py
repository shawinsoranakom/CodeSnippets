def try_import_cutlass() -> bool:
    """
    We want to support three ways of passing in CUTLASS:
    1. fbcode, handled by the internal build system.
    2. User specifies cutlass_dir. The default is ../third_party/cutlass/,
       which is the directory when developers build from source.
    """
    if config.is_fbcode():
        try:
            import cutlass_cppgen  # type: ignore[import-not-found]
            import cutlass_library  # type: ignore[import-not-found]
        except ImportError as e:
            log.warning(
                "Failed to import CUTLASS packages in fbcode: %s, ignoring the CUTLASS backend.",
                e,
            )
            return False

        return True

    # Copy CUTLASS python scripts to a temp dir and add the temp dir to Python search path.
    # This is a temporary hack to avoid CUTLASS module naming conflicts.
    # TODO(ipiszy): remove this hack when CUTLASS solves Python scripts packaging structure issues.

    # TODO(mlazos): epilogue visitor tree currently lives in python/cutlass,
    # but will be moved to python/cutlass_library in the future (later 2025)
    def path_join(path0, path1):
        return os.path.abspath(os.path.join(path0, path1))

    # contains both cutlass and cutlass_library
    # we need cutlass for eVT
    cutlass_dir = (
        config.xpu.cutlass_dir
        if torch.xpu._is_compiled()
        else config.cutlass.cutlass_dir
    )
    cutlass_python_path = path_join(cutlass_dir, "python")
    torch_root = os.path.abspath(os.path.dirname(torch.__file__))
    mock_src_path = os.path.join(
        torch_root,
        "_inductor",
        "codegen",
        "cutlass",
        "lib_extensions",
        "cutlass_mock_imports",
    )

    cutlass_library_src_path = path_join(cutlass_python_path, "cutlass_library")
    cutlass_cppgen_src_path = path_join(cutlass_python_path, "cutlass_cppgen")
    pycute_src_path = path_join(cutlass_python_path, "pycute")

    tmp_cutlass_full_path = os.path.abspath(os.path.join(cache_dir(), "torch_cutlass"))

    dst_link_library = path_join(tmp_cutlass_full_path, "cutlass_library")
    dst_link_cutlass_cppgen = path_join(tmp_cutlass_full_path, "cutlass_cppgen")
    dst_link_pycute = path_join(tmp_cutlass_full_path, "pycute")

    # mock modules to import cutlass
    mock_modules = ["cuda", "scipy", "pydot"]

    if os.path.isdir(cutlass_python_path):
        if tmp_cutlass_full_path not in sys.path:

            def link_and_append(dst_link, src_path, parent_dir):
                if os.path.lexists(dst_link):
                    assert os.path.islink(dst_link), (
                        f"{dst_link} is not a symlink. Try to remove {dst_link} manually and try again."
                    )
                    assert os.path.realpath(os.readlink(dst_link)) == os.path.realpath(
                        src_path,
                    ), f"Symlink at {dst_link} does not point to {src_path}"
                else:
                    os.makedirs(parent_dir, exist_ok=True)
                    os.symlink(src_path, dst_link)

                if parent_dir not in sys.path:
                    sys.path.append(parent_dir)

            link_and_append(
                dst_link_library, cutlass_library_src_path, tmp_cutlass_full_path
            )
            link_and_append(
                dst_link_cutlass_cppgen, cutlass_cppgen_src_path, tmp_cutlass_full_path
            )
            link_and_append(dst_link_pycute, pycute_src_path, tmp_cutlass_full_path)

            for module in mock_modules:
                link_and_append(
                    path_join(tmp_cutlass_full_path, module),  # dst_link
                    path_join(mock_src_path, module),  # src_path
                    tmp_cutlass_full_path,  # parent
                )

        try:
            import cutlass_cppgen  # type: ignore[import-not-found]  # noqa: F401
            import cutlass_library.generator
            import cutlass_library.library
            import cutlass_library.manifest  # noqa: F401
            import pycute  # type: ignore[import-not-found]  # noqa: F401

            return True
        except ImportError as e:
            log.debug(
                "Failed to import CUTLASS packages: %s, ignoring the CUTLASS backend.",
                e,
            )
    else:
        log.debug(
            "Failed to import CUTLASS packages: CUTLASS repo does not exist: %s",
            cutlass_python_path,
        )
    return False