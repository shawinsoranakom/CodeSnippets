def generate(
        self,
        version: str | None,
        cmake_python_library: str | None,
        build_python: bool,
        build_test: bool,
        my_env: dict[str, str],
        rerun: bool,
    ) -> None:
        """Runs cmake to generate native build files."""

        if rerun and os.path.isfile(self._cmake_cache_file):
            os.remove(self._cmake_cache_file)

        cmake_cache_file_available = os.path.exists(self._cmake_cache_file)
        if cmake_cache_file_available:
            cmake_cache_variables = self.get_cmake_cache_variables()
            make_program: str | None = cmake_cache_variables.get("CMAKE_MAKE_PROGRAM")  # type: ignore[assignment]
            if make_program and not shutil.which(make_program):
                # CMakeCache.txt exists, but the make program (e.g., ninja) does not.
                # See also: https://github.com/astral-sh/uv/issues/14269
                # This can happen if building with PEP-517 build isolation, where `ninja` was
                # installed in the isolated environment of the previous build run, but it has been
                # removed. The `ninja` executable with an old absolute path not available anymore.
                eprint(
                    "!!!WARNING!!!: CMakeCache.txt exists, "
                    f"but CMAKE_MAKE_PROGRAM ({make_program!r}) does not exist. "
                    "Clearing CMake cache."
                )
                self.clear_cache()
                cmake_cache_file_available = False
            elif (
                cached_python := cmake_cache_variables.get("Python_EXECUTABLE")
            ) and cached_python != sys.executable:
                # Drop all Python_* cache entries (including FindPython's INTERNAL
                # `_Python_*` copies) so find_package(Python) re-detects headers,
                # libraries, and NumPy paths for the new interpreter. Without
                # this, Python-linked targets relink against stale headers and
                # produce wheels that fail to import. Non-Python entries stay,
                # so we skip a full reconfigure.
                eprint(
                    "!!!WARNING!!!: Python interpreter changed "
                    f"({cached_python!r} -> {sys.executable!r}). "
                    "Dropping Python_* cache entries."
                )
                python_name_re = re.compile(r"^_?(?:Python|PYTHON)[23]?_")
                self._remove_cache_entries(
                    [
                        name
                        for name in self._cache_variable_names()
                        if python_name_re.match(name)
                    ]
                )
                cmake_cache_file_available = False

        if cmake_cache_file_available and (
            not USE_NINJA or os.path.exists(self._ninja_build_file)
        ):
            # Everything's in place. Do not rerun.
            return

        args = []
        if USE_NINJA:
            # Avoid conflicts in '-G' and the `CMAKE_GENERATOR`
            os.environ["CMAKE_GENERATOR"] = "Ninja"
            args.append("-GNinja")
        elif IS_WINDOWS:
            generator = os.getenv("CMAKE_GENERATOR", "Visual Studio 16 2019")
            supported = ["Visual Studio 16 2019", "Visual Studio 17 2022"]
            if generator not in supported:
                eprint("Unsupported `CMAKE_GENERATOR`: " + generator)
                eprint("Please set it to one of the following values: ")
                eprint("\n".join(supported))
                sys.exit(1)
            args.append("-G" + generator)
            toolset_dict = {}
            toolset_version = os.getenv("CMAKE_GENERATOR_TOOLSET_VERSION")
            if toolset_version is not None:
                toolset_dict["version"] = toolset_version
                curr_toolset = os.getenv("VCToolsVersion")
                if curr_toolset is None:
                    eprint(
                        "When you specify `CMAKE_GENERATOR_TOOLSET_VERSION`, you must also "
                        "activate the vs environment of this version. Please read the notes "
                        "in the build steps carefully."
                    )
                    sys.exit(1)
            if IS_64BIT:
                if platform.machine() == "ARM64":
                    args.append("-A ARM64")
                else:
                    args.append("-Ax64")
                    toolset_dict["host"] = "x64"
            if toolset_dict:
                toolset_expr = ",".join([f"{k}={v}" for k, v in toolset_dict.items()])
                args.append("-T" + toolset_expr)

        # base_dir is used as cmake's source-dir arg and install prefix;
        # make it relative to build_dir so these are worktree-independent
        # (ccache/re-cc friendly).  cmake runs with cwd=build_dir so the
        # relative path resolves correctly.
        base_dir = str(Path(__file__).absolute().parents[2])
        if os.environ.get("USE_RELATIVE_PATHS"):
            base_dir = os.path.relpath(
                str(Path(__file__).resolve().parents[2]), self.build_dir
            )
        install_dir = os.path.join(base_dir, "torch")

        _mkdir_p(install_dir)
        _mkdir_p(self.build_dir)

        # Environment variable forwarding (BUILD_*, USE_*, CMAKE_*, aliases,
        # passthrough vars, CMAKE_PREFIX_PATH, low-priority aliases) is now
        # handled by cmake/EnvVarForwarding.cmake, which is included early in
        # the top-level CMakeLists.txt. Only options that require Python-side
        # detection are passed here.

        build_options: dict[str, CMakeValue] = {
            "CMAKE_INSTALL_PREFIX": install_dir,
            "BUILD_PYTHON": build_python,
            "BUILD_TEST": build_test,
        }

        use_numpy = not check_negative_env_flag("USE_NUMPY")
        build_options["USE_NUMPY"] = use_numpy
        if use_numpy:
            try:
                import numpy

                build_options["Python_NumPy_INCLUDE_DIR"] = numpy.get_include()
            except ImportError:
                pass

        # NVSHMEM detection from Python lib path
        py_lib_path = sysconfig.get_path("purelib")
        nvshmem_py_dir = py_lib_path + "/nvidia/nvshmem"
        if os.path.exists(nvshmem_py_dir):
            build_options["NVSHMEM_PY_DIR"] = nvshmem_py_dir

        CMake.defines(
            args,
            Python_EXECUTABLE=sys.executable,
            TORCH_BUILD_VERSION=version,
            **build_options,
        )

        expected_wrapper = "/usr/local/opt/ccache/libexec"
        if IS_DARWIN and os.path.exists(expected_wrapper):
            if "CMAKE_C_COMPILER" not in build_options and "CC" not in os.environ:
                CMake.defines(args, CMAKE_C_COMPILER=f"{expected_wrapper}/gcc")
            if "CMAKE_CXX_COMPILER" not in build_options and "CXX" not in os.environ:
                CMake.defines(args, CMAKE_CXX_COMPILER=f"{expected_wrapper}/g++")

        for env_var_name in my_env:
            if env_var_name.startswith("gh"):
                # github env vars use utf-8, on windows, non-ascii code may
                # cause problem, so encode first
                try:
                    my_env[env_var_name] = str(my_env[env_var_name].encode("utf-8"))
                except UnicodeDecodeError as e:
                    shex = ":".join(f"{ord(c):02x}" for c in my_env[env_var_name])
                    eprint(f"Invalid ENV[{env_var_name}] = {shex}")
                    eprint(e)
        # According to the CMake manual, we should pass the arguments first,
        # and put the directory as the last element. Otherwise, these flags
        # may not be passed correctly.
        # Reference:
        # 1. https://cmake.org/cmake/help/latest/manual/cmake.1.html#synopsis
        # 2. https://stackoverflow.com/a/27169347
        args.append(base_dir)
        self.run(args, env=my_env)