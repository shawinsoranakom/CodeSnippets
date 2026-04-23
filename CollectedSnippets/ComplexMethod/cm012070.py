def __init__(
        self,
        name: str,
        sources: str | list[str],
        BuildOption: BuildOptionsBase,
        output_dir: str = "",
    ) -> None:
        self._compiler = ""
        self._cflags_args = ""
        self._definitions_args = ""
        self._include_dirs_args = ""
        self._ldflags_args = ""
        self._libraries_dirs_args = ""
        self._libraries_args = ""
        self._passthrough_parameters_args = ""

        # When relative path is used, we need to maintain the source dir list.
        self._orig_source_paths = []
        self._output_dir = ""
        self._target_file = ""

        self._use_relative_path: bool = False
        self._aot_mode: bool = False

        self._name = name
        self._target_name = (
            config.aot_inductor.model_name_for_generated_files or "aoti_model"
        )

        # Code start here, initial self internal variables firstly.
        self._build_option = BuildOption
        self._compiler = BuildOption.get_compiler()
        self._use_relative_path = BuildOption.get_use_relative_path()
        self._aot_mode = BuildOption.get_aot_mode()

        self._output_dir = output_dir

        self._compile_only = BuildOption.get_compile_only()
        self._precompiling = BuildOption.get_precompiling()
        self._preprocessing = BuildOption.get_preprocessing()
        # Only one of these options (if any) should be true at any given time.
        assert sum((self._compile_only, self._precompiling, self._preprocessing)) <= 1
        self._do_link = not (
            self._compile_only or self._precompiling or self._preprocessing
        )

        # MSVC produces two files when precompiling: the actual .pch file, as well as an
        # object file which must be linked into the final library.  This class assumes
        # only one output file of note, so for now we'll error out here.
        assert not _IS_WINDOWS or not self._precompiling, (
            "Cannot currently precompile headers on Windows!"
        )

        if self._compile_only:
            file_ext, output_flags = self.__get_object_flags()
        elif self._precompiling:
            file_ext, output_flags = self.__get_precompiled_header_flags()
        elif self._preprocessing:
            file_ext, output_flags = self.__get_preprocessor_output_flags()
        else:
            file_ext, output_flags = self.__get_python_module_flags()
        self._target_file = os.path.join(self._output_dir, f"{self._name}{file_ext}")

        relative_target_file = (
            os.path.basename(self._target_file)
            if self._use_relative_path
            else self._target_file
        )
        if _IS_WINDOWS:
            if self._preprocessing:
                # The target file name is automatically determined by MSVC.
                self._output = output_flags
            else:
                self._output = f"{output_flags}{relative_target_file}"
        else:
            self._output = f"{output_flags} {relative_target_file}"

        if isinstance(sources, str):
            sources = [sources]

        # Use relative paths only when requested (typically for remote builds)
        if config.is_fbcode() and self._use_relative_path:
            # Will create another temp directory for building, so do NOT use the
            # absolute path.
            self._orig_source_paths = list(sources)
            sources = [os.path.basename(i) for i in sources]

        if self._precompiling:
            assert len(sources) == 1
            # See above; we can currently assume this is not on MSVC.
            self._sources_args = f"-x c++-header {sources[0]}"
            if self._use_relative_path and _is_clang(BuildOption.get_compiler()):
                # Store PCH paths relative to -isysroot so the .pch can
                # be used from a different build directory.  The matching
                # -isysroot is injected by build_fbcode_re().
                self._cflags_args += " -relocatable-pch -Xclang -fno-pch-timestamp "
        else:
            self._sources_args = " ".join(sources)

        for cflag in BuildOption.get_cflags():
            if _IS_WINDOWS:
                self._cflags_args += f"/{cflag} "
            else:
                self._cflags_args += f"-{cflag} "

        for definition in BuildOption.get_definitions():
            if _IS_WINDOWS:
                self._definitions_args += f"/D {definition} "
            else:
                self._definitions_args += f"-D {definition} "

        if precompiled_header := BuildOption.precompiled_header:
            if _IS_WINDOWS:
                log.warning(
                    "Precompiled header support for MSVC is currently unavailable; ignoring %s",
                    precompiled_header,
                )
            else:
                self._include_dirs_args = f"-include {precompiled_header} "
                if self._use_relative_path and _is_clang(BuildOption.get_compiler()):
                    # Skip clang's own PCH validation during consumption.
                    # _precompile_header() already handles cache invalidation
                    # via content hashing, and -fno-validate-pch allows the
                    # PCH to be used even when the original source file is at
                    # a different path (e.g. across Remote Execution workers).
                    self._cflags_args += " -Xclang -fno-validate-pch "

        for inc_dir in BuildOption.get_include_dirs():
            if _IS_WINDOWS:
                self._include_dirs_args += f'/I "{inc_dir}" '
            else:
                self._include_dirs_args += f"-I{shlex.quote(inc_dir)} "

        for ldflag in BuildOption.get_ldflags():
            if _IS_WINDOWS:
                self._ldflags_args += f"/{ldflag} "
            else:
                self._ldflags_args += f"-{ldflag} "

        for lib_dir in BuildOption.get_libraries_dirs():
            if _IS_WINDOWS:
                self._libraries_dirs_args += f'/LIBPATH:"{lib_dir}" '
            else:
                self._libraries_dirs_args += f"-L{lib_dir} "

        for lib in BuildOption.get_libraries():
            if _IS_WINDOWS:
                self._libraries_args += f'"{lib}.lib" '
            else:
                self._libraries_args += f"-l{lib} "

        for passthrough_arg in BuildOption.get_passthrough_args():
            self._passthrough_parameters_args += f"{passthrough_arg} "