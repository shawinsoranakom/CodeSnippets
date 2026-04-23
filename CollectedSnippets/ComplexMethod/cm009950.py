def main() -> None:
    if BUILD_LIBTORCH_WHL and BUILD_PYTHON_ONLY:
        raise RuntimeError(
            "Conflict: 'BUILD_LIBTORCH_WHL' and 'BUILD_PYTHON_ONLY' can't both be 1. "
            "Set one to 0 and rerun."
        )

    install_requires = [
        "filelock",
        "typing-extensions>=4.10.0",
        "setuptools<82",
        "sympy>=1.13.3",
        "networkx>=2.5.1",
        "jinja2",
        "fsspec>=0.8.5",
    ]
    if BUILD_PYTHON_ONLY:
        install_requires += [f"{LIBTORCH_PKG_NAME}=={TORCH_VERSION}"]

    # Parse the command line and check the arguments before we proceed with
    # building deps and setup. We need to set values so `--help` works.
    dist = Distribution()
    dist.script_name = os.path.basename(sys.argv[0])
    dist.script_args = sys.argv[1:]
    try:
        dist.parse_command_line()
    except setuptools.errors.BaseError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    mirror_files_into_torchgen()
    if RUN_BUILD_DEPS:
        build_deps()
        mirror_inductor_external_kernels()

    (
        ext_modules,
        cmdclass,
        packages,
        entry_points,
        extra_install_requires,
    ) = configure_extension_build()
    install_requires += extra_install_requires

    torch_package_data = [
        "py.typed",
        "bin/*",
        "test/*",
        "*.pyi",
        "**/*.pyi",
        "lib/*.pdb",
        "lib/**/*.pdb",
        "lib/*shm*",
        "lib/torch_shm_manager",
        "lib/*.h",
        "lib/**/*.h",
        "include/*.h",
        "include/**/*.h",
        "include/*.hpp",
        "include/**/*.hpp",
        "include/*.cuh",
        "include/**/*.cuh",
        "csrc/inductor/aoti_runtime/model.h",
        "_inductor/codegen/*.h",
        "_inductor/codegen/aoti_runtime/*.h",
        "_inductor/codegen/aoti_runtime/*.cpp",
        "_inductor/script.ld",
        "_inductor/kernel/flex/templates/*.jinja",
        "_inductor/kernel/templates/*.jinja",
        "_export/serde/*.yaml",
        "_export/serde/*.thrift",
        "share/cmake/ATen/*.cmake",
        "share/cmake/Caffe2/*.cmake",
        "share/cmake/Caffe2/public/*.cmake",
        "share/cmake/Caffe2/Modules_CUDA_fix/*.cmake",
        "share/cmake/Caffe2/Modules_CUDA_fix/upstream/*.cmake",
        "share/cmake/Caffe2/Modules_CUDA_fix/upstream/FindCUDA/*.cmake",
        "share/cmake/Gloo/*.cmake",
        "share/cmake/Tensorpipe/*.cmake",
        "share/cmake/Torch/*.cmake",
        "utils/benchmark/utils/*.cpp",
        "utils/benchmark/utils/valgrind_wrapper/*.cpp",
        "utils/benchmark/utils/valgrind_wrapper/*.h",
        "utils/model_dump/skeleton.html",
        "utils/model_dump/code.js",
        "utils/model_dump/*.mjs",
        "_dynamo/graph_break_registry.json",
        "tools/dynamo/gb_id_mapping.py",
    ]

    if not BUILD_LIBTORCH_WHL:
        torch_package_data += [
            "lib/libtorch_python.so",
            "lib/libtorch_python.dylib",
            "lib/libtorch_python.dll",
        ]
    if not BUILD_PYTHON_ONLY:
        torch_package_data += [
            "lib/*.so*",
            "lib/*.dylib*",
            "lib/*.dll",
            "lib/*.lib",
        ]
        # XXX: Why not use wildcards ["lib/aotriton.images/*", "lib/aotriton.images/**/*"] here?
        aotriton_image_path = TORCH_DIR / "lib" / "aotriton.images"
        aks2_files = [
            file.relative_to(TORCH_DIR).as_posix()
            for file in aotriton_image_path.rglob("*")
            if file.is_file()
        ]
        torch_package_data += aks2_files
    if get_cmake_cache_vars()["USE_TENSORPIPE"]:
        torch_package_data += [
            "include/tensorpipe/*.h",
            "include/tensorpipe/**/*.h",
        ]
    if get_cmake_cache_vars()["USE_KINETO"]:
        torch_package_data += [
            "include/kineto/*.h",
            "include/kineto/**/*.h",
        ]
    torchgen_package_data = [
        "packaged/*",
        "packaged/**/*",
    ]
    package_data = {
        "torch": torch_package_data,
    }
    # some win libraries are excluded
    # these are statically linked
    exclude_windows_libs = [
        "lib/dnnl.lib",
        "lib/kineto.lib",
        "lib/libprotobuf-lite.lib",
        "lib/libprotobuf.lib",
        "lib/libprotoc.lib",
    ]
    exclude_package_data = {
        "torch": exclude_windows_libs,
    }

    if not BUILD_LIBTORCH_WHL:
        package_data["torchgen"] = torchgen_package_data
        exclude_package_data["torchgen"] = ["*.py[co]"]
    else:
        # no extensions in BUILD_LIBTORCH_WHL mode
        ext_modules = []

    setup(
        name=TORCH_PACKAGE_NAME,
        version=TORCH_VERSION,
        ext_modules=ext_modules,
        cmdclass=cmdclass,
        packages=packages,
        entry_points=entry_points,
        install_requires=install_requires,
        package_data=package_data,
        exclude_package_data=exclude_package_data,
        # Disable automatic inclusion of data files because we want to
        # explicitly control with `package_data` above.
        include_package_data=False,
    )
    if EMIT_BUILD_WARNING:
        print_box(build_update_message)