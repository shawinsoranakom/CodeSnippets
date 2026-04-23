def _test_cpp_extensions_aot(test_directory, options, use_ninja):
    if use_ninja:
        try:
            from torch.utils import cpp_extension

            cpp_extension.verify_ninja_availability()
        except RuntimeError:
            print_to_stderr(CPP_EXTENSIONS_ERROR)
            return 1

    # Wipe the build folder, if it exists already
    cpp_extensions_test_dir = os.path.join(test_directory, "cpp_extensions")
    cpp_extensions_test_build_dir = os.path.join(cpp_extensions_test_dir, "build")
    if os.path.exists(cpp_extensions_test_build_dir):
        shutil.rmtree(cpp_extensions_test_build_dir)

    # Build the test cpp extensions modules
    shell_env = os.environ.copy()
    shell_env["USE_NINJA"] = str(1 if use_ninja else 0)
    install_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-build-isolation",
        ".",
        "--root",
        "./install",
    ]
    wheel_cmd = [sys.executable, "-m", "build", "--wheel", "--no-isolation"]
    return_code = shell(install_cmd, cwd=cpp_extensions_test_dir, env=shell_env)
    if return_code != 0:
        return return_code
    if sys.platform != "win32":
        exts_to_build = [
            (install_cmd, "no_python_abi_suffix_test"),
        ]
        if TEST_CUDA or TEST_XPU:
            exts_to_build.append((wheel_cmd, "python_agnostic_extension"))
        if TEST_CUDA:
            exts_to_build.append((install_cmd, "libtorch_agn_2_9_extension"))
            exts_to_build.append((install_cmd, "libtorch_agn_2_10_extension"))
        for cmd, extension_dir in exts_to_build:
            return_code = shell(
                cmd,
                cwd=os.path.join(cpp_extensions_test_dir, extension_dir),
                env=shell_env,
            )
            if return_code != 0:
                return return_code

    from shutil import copyfile

    os.environ["USE_NINJA"] = shell_env["USE_NINJA"]
    test_module = "test_cpp_extensions_aot" + ("_ninja" if use_ninja else "_no_ninja")
    copyfile(
        test_directory + "/test_cpp_extensions_aot.py",
        test_directory + "/" + test_module + ".py",
    )

    try:
        cpp_extensions = os.path.join(test_directory, "cpp_extensions")
        install_directories = []
        # install directory is the one that is named site-packages
        for root, directories, _ in os.walk(os.path.join(cpp_extensions, "install")):
            for directory in directories:
                if "-packages" in directory:
                    install_directories.append(os.path.join(root, directory))

        for extension_name in [
            "libtorch_agn_2_9_extension",
            "libtorch_agn_2_10_extension",
        ]:
            for root, directories, _ in os.walk(
                os.path.join(cpp_extensions, extension_name, "install")
            ):
                for directory in directories:
                    if "-packages" in directory:
                        install_directories.append(os.path.join(root, directory))

        with extend_python_path(install_directories):
            return run_test(ShardedTest(test_module, 1, 1), test_directory, options)
    finally:
        if os.path.exists(test_directory + "/" + test_module + ".py"):
            os.remove(test_directory + "/" + test_module + ".py")
        os.environ.pop("USE_NINJA")