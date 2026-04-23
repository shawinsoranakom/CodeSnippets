def _get_openmp_args(
    cpp_compiler: str,
) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str]]:
    cflags: list[str] = []
    ldflags: list[str] = []
    include_dir_paths: list[str] = []
    lib_dir_paths: list[str] = []
    libs: list[str] = []
    passthrough_args: list[str] = []

    if config.aot_inductor.cross_target_platform == "windows":
        return cflags, ldflags, include_dir_paths, lib_dir_paths, libs, passthrough_args
    if _IS_MACOS:
        # Per https://mac.r-project.org/openmp/ right way to pass `openmp` flags to MacOS is via `-Xclang`
        cflags.append("Xclang")
        cflags.append("fopenmp")

        # only Apple builtin compilers (Apple Clang++) require openmp
        omp_available = not _is_apple_clang(cpp_compiler)

        # check the `OMP_PREFIX` environment first
        omp_prefix = os.getenv("OMP_PREFIX")
        if omp_prefix is not None:
            header_path = os.path.join(omp_prefix, "include", "omp.h")
            valid_env = os.path.exists(header_path)
            if valid_env:
                include_dir_paths.append(os.path.join(omp_prefix, "include"))
                lib_dir_paths.append(os.path.join(omp_prefix, "lib"))
            else:
                warnings.warn("environment variable `OMP_PREFIX` is invalid.")
            omp_available = omp_available or valid_env

        if not omp_available:
            libs.append("omp")

        # prefer to use openmp from `conda install llvm-openmp`
        conda_prefix = os.getenv("CONDA_PREFIX")
        if not omp_available and conda_prefix is not None:
            omp_available = is_conda_llvm_openmp_installed()
            if omp_available:
                conda_lib_path = os.path.join(conda_prefix, "lib")
                include_dir_paths.append(os.path.join(conda_prefix, "include"))
                lib_dir_paths.append(conda_lib_path)
                # Prefer Intel OpenMP on x86 machine
                if os.uname().machine == "x86_64" and os.path.exists(
                    os.path.join(conda_lib_path, "libiomp5.dylib")
                ):
                    libs.append("iomp5")

        # next, try to use openmp from `brew install libomp`
        if not omp_available:
            omp_available, libomp_path = homebrew_libomp()
            if omp_available:
                include_dir_paths.append(os.path.join(libomp_path, "include"))
                lib_dir_paths.append(os.path.join(libomp_path, "lib"))

        # if openmp is still not available, we let the compiler to have a try,
        # and raise error together with instructions at compilation error later
    elif _IS_WINDOWS:
        """
        On Windows, `clang` and `icx` have their specific openmp implenmention.
        And the openmp lib is in compiler's some sub-directory.
        For dynamic library(DLL) load, the Windows native APIs are `LoadLibraryA` and `LoadLibraryExA`, and their search
        dependencies have some rules:
        https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibraryexa#searching-for-dlls-and-dependencies
        In some case, the rules may not include compiler's sub-directories.
        So, it can't search and load compiler's openmp library correctly.
        And then, the whole application would be broken.

        To avoid the openmp load failed, we can automatic locate the openmp binary and preload it.
        1. For clang, the function is `perload_clang_libomp_win`.
        2. For icx, the function is `perload_icx_libomp_win`.
        """
        if _is_clang(cpp_compiler):
            cflags.append("openmp")
            libs.append("libomp")
            perload_clang_libomp_win(cpp_compiler, "libomp.dll")
        elif _is_intel_compiler(cpp_compiler):
            cflags.append("Qiopenmp")
            libs.append("libiomp5md")
            perload_icx_libomp_win(cpp_compiler)
        else:
            # /openmp, /openmp:llvm
            # llvm on Windows, new openmp: https://devblogs.microsoft.com/cppblog/msvc-openmp-update/
            # msvc openmp: https://learn.microsoft.com/zh-cn/cpp/build/reference/openmp-enable-openmp-2-0-support?view=msvc-170
            cflags.append("openmp")
            cflags.append("openmp:experimental")  # MSVC CL
    else:
        if config.is_fbcode():
            include_dir_paths.append(build_paths.openmp_include)

            passthrough_args.append("-Wp,-fopenmp")
            lib_dir_paths.append(os.path.dirname(build_paths.openmp_lib_so))

            libs.append("omp")
        else:
            if _is_clang(cpp_compiler):
                # TODO: fix issue, can't find omp.h
                cflags.append("fopenmp")
                libs.append("gomp")
            elif _is_intel_compiler(cpp_compiler):
                cflags.append("fiopenmp")
            else:
                cflags.append("fopenmp")
                libs.append("gomp")

    return cflags, ldflags, include_dir_paths, lib_dir_paths, libs, passthrough_args