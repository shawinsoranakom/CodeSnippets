def build_deps() -> None:
    report(f"-- Building version {TORCH_VERSION}")

    # ATTENTION: THIS IS AI SLOP
    # Check for USE_NIGHTLY=VERSION to bypass normal build and download nightly wheel
    nightly_version = os.getenv("USE_NIGHTLY")
    if nightly_version is not None:
        import re

        if (
            nightly_version == ""
            or nightly_version == "cpu"
            or re.match(r"^cu\d+$", nightly_version)
            or re.match(r"^rocm\d+\.\d+$", nightly_version)
        ):
            # Empty string or variant-only specification, show error with latest version
            variant = "cpu" if nightly_version == "" else nightly_version
            report(f"-- Detecting latest {variant} nightly version...")
            latest_version = get_latest_nightly_version(variant)
            # Also get the git hash to tell user which commit to checkout
            git_hash = get_nightly_git_hash(latest_version)

            if nightly_version == "":
                error_msg = f"USE_NIGHTLY cannot be empty. Latest available version: {latest_version}\n"
            else:
                error_msg = (
                    "USE_NIGHTLY requires a specific version, not just a variant. "
                    "Latest available {nightly_version} version: {latest_version}\n"
                )

            error_msg += f'Try: USE_NIGHTLY="{latest_version}"'
            error_msg += f"\n\nIMPORTANT: You must checkout the matching source commit for this binary:\ngit checkout {git_hash}"
            raise RuntimeError(error_msg)
        else:
            # Full version specification
            report(
                f"-- USE_NIGHTLY={nightly_version} detected, downloading nightly wheel"
            )
            download_and_extract_nightly_wheel(nightly_version)
            return

    check_submodules()
    check_pydep("yaml", "pyyaml")
    build_pytorch(
        version=TORCH_VERSION,
        cmake_python_library=CMAKE_PYTHON_LIBRARY.as_posix(),
        build_python=not BUILD_LIBTORCH_WHL,
        rerun_cmake=RERUN_CMAKE,
        cmake_only=CMAKE_ONLY,
        cmake=cmake,
    )

    if CMAKE_ONLY:
        report(
            'Finished running cmake. Run "ccmake build" or '
            '"cmake-gui build" to adjust build options and '
            '"python -m pip install --no-build-isolation -v ." to build.'
        )
        sys.exit()

    # Use copies instead of symbolic files.
    # Windows has very poor support for them.
    sym_files = [
        CWD / "tools/shared/_utils_internal.py",
        CWD / "torch/utils/benchmark/utils/valgrind_wrapper/callgrind.h",
        CWD / "torch/utils/benchmark/utils/valgrind_wrapper/valgrind.h",
    ]
    orig_files = [
        CWD / "torch/_utils_internal.py",
        CWD / "third_party/valgrind-headers/callgrind.h",
        CWD / "third_party/valgrind-headers/valgrind.h",
    ]
    for sym_file, orig_file in zip(sym_files, orig_files):
        same = False
        if sym_file.exists():
            if filecmp.cmp(sym_file, orig_file):
                same = True
            else:
                sym_file.unlink()
        if not same:
            shutil.copyfile(orig_file, sym_file)