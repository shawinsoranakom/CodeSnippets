def configure_extension_build() -> tuple[
    list[Extension],  # ext_modules
    dict[str, type[Command]],  # cmdclass
    list[str],  # packages
    dict[str, list[str]],  # entry_points
    list[str],  # extra_install_requires
]:
    r"""Configures extension build options according to system environment and user's choice.

    Returns:
      The input to parameters ext_modules, cmdclass, packages, and entry_points as required in setuptools.setup.
    """

    cmake_cache_vars = get_cmake_cache_vars()

    ################################################################################
    # Configure compile flags
    ################################################################################

    library_dirs: list[str] = [str(TORCH_LIB_DIR)]
    extra_install_requires: list[str] = []

    if IS_WINDOWS:
        # /NODEFAULTLIB makes sure we only link to DLL runtime
        # and matches the flags set for protobuf and ONNX
        extra_link_args: list[str] = ["/NODEFAULTLIB:LIBCMT.LIB"]
        # /MD links against DLL runtime
        # and matches the flags set for protobuf and ONNX
        # /EHsc is about standard C++ exception handling
        extra_compile_args: list[str] = ["/MD", "/FS", "/EHsc"]
    else:
        extra_link_args = []
        extra_compile_args = [
            "-Wall",
            "-Wextra",
            "-Wno-strict-overflow",
            "-Wno-unused-parameter",
            "-Wno-missing-field-initializers",
            "-Wno-unknown-pragmas",
            # Python 2.6 requires -fno-strict-aliasing, see
            # http://legacy.python.org/dev/peps/pep-3123/
            # We also depend on it in our code (even Python 3).
            "-fno-strict-aliasing",
        ]

    main_compile_args: list[str] = []
    main_libraries: list[str] = ["torch_python"]

    main_link_args: list[str] = []
    main_sources: list[str] = ["torch/csrc/stub.c"]

    if BUILD_LIBTORCH_WHL:
        main_libraries = ["torch"]
        main_sources = []

    if build_type.is_debug():
        if IS_WINDOWS:
            extra_compile_args += ["/Z7"]
            extra_link_args += ["/DEBUG:FULL"]
        else:
            extra_compile_args += ["-O0", "-g"]
            extra_link_args += ["-O0", "-g"]

    if build_type.is_rel_with_deb_info():
        if IS_WINDOWS:
            extra_compile_args += ["/Z7"]
            extra_link_args += ["/DEBUG:FULL"]
        else:
            extra_compile_args += ["-g"]
            extra_link_args += ["-g"]

    # pypi cuda package that requires installation of cuda runtime, cudnn and cublas
    # should be included in all wheels uploaded to pypi
    pytorch_extra_install_requires = os.getenv("PYTORCH_EXTRA_INSTALL_REQUIREMENTS")
    if pytorch_extra_install_requires:
        report(f"pytorch_extra_install_requirements: {pytorch_extra_install_requires}")
        extra_install_requires.extend(
            map(str.strip, pytorch_extra_install_requires.split("|"))
        )

    # Cross-compile for M1
    if IS_DARWIN:
        macos_target_arch = os.getenv("CMAKE_OSX_ARCHITECTURES", "")
        if macos_target_arch in ["arm64", "x86_64"]:
            macos_sysroot_path = os.getenv("CMAKE_OSX_SYSROOT")
            if macos_sysroot_path is None:
                macos_sysroot_path = (
                    subprocess.check_output(
                        ["xcrun", "--show-sdk-path", "--sdk", "macosx"]
                    )
                    .decode("utf-8")
                    .strip()
                )
            extra_compile_args += [
                "-arch",
                macos_target_arch,
                "-isysroot",
                macos_sysroot_path,
            ]
            extra_link_args += ["-arch", macos_target_arch]

    def make_relative_rpath_args(path: str) -> list[str]:
        if IS_DARWIN:
            return ["-Wl,-rpath,@loader_path/" + path]
        elif IS_WINDOWS:
            return []
        else:
            return ["-Wl,-rpath,$ORIGIN/" + path]

    ################################################################################
    # Declare extensions and package
    ################################################################################

    ext_modules: list[Extension] = []
    # packages that we want to install into site-packages and include them in wheels
    includes = ["torch", "torch.*", "torchgen", "torchgen.*"]
    # exclude folders that they look like Python packages but are not wanted in wheels
    excludes = ["tools", "tools.*", "caffe2", "caffe2.*"]
    if cmake_cache_vars["BUILD_FUNCTORCH"]:
        includes.extend(["functorch", "functorch.*"])
    else:
        excludes.extend(["functorch", "functorch.*"])
    packages = find_packages(include=includes, exclude=excludes)
    C = Extension(
        "torch._C",
        libraries=main_libraries,
        sources=main_sources,
        language="c",
        extra_compile_args=[
            *main_compile_args,
            *extra_compile_args,
        ],
        include_dirs=[],
        library_dirs=library_dirs,
        extra_link_args=[
            *extra_link_args,
            *main_link_args,
            *make_relative_rpath_args("lib"),
        ],
    )
    ext_modules.append(C)

    cmdclass = {
        "bdist_wheel": bdist_wheel,
        "build_ext": build_ext,
        "clean": clean,
        "sdist": sdist,
    }

    entry_points = {
        "console_scripts": [
            "torchrun = torch.distributed.run:main",
        ],
        "torchrun.logs_specs": [
            "default = torch.distributed.elastic.multiprocessing:DefaultLogsSpecs",
        ],
    }

    if cmake_cache_vars["USE_DISTRIBUTED"]:
        # Only enable fr_trace command if distributed is enabled
        entry_points["console_scripts"].append(
            "torchfrtrace = torch.distributed.flight_recorder.fr_trace:main",
        )
    return ext_modules, cmdclass, packages, entry_points, extra_install_requires