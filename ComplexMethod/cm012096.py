def load_async(
        cls,
        main_code: str,
        device_type: str = "cpu",
        submit_fn: Any = None,
        extra_flags: Sequence[str] = (),
        optimized_code: str | None = None,
    ) -> Any:
        """Compile and load a C++ library.  Returns a callable that returns the loaded
        library."""
        compile_command = {
            **cls.cpp_compile_command_flags,
            "device_type": device_type,
            "extra_flags": extra_flags,
            "use_relative_path": config.is_fbcode(),
            "vec_isa": pick_vec_isa(),
        }

        _set_gpu_runtime_env()  # cpp_extension consults the env

        # Note the distinction between the two booleans.  We do minimal optimization if
        # the optimized_code argument is present at all, since that's how the user of
        # this function opts in, but we do compilation and linking in one step if the
        # optimized_code argument is empty (as a micro-optimization).
        # On GPU the C++ wrapper is just glue — the real kernels are compiled
        # separately by Triton/CUDA.  Always use -O1 to cut compile time.
        min_optimize = optimized_code is not None or device_type != "cpu"
        main_build_option = CppTorchDeviceOptions(
            compile_only=bool(optimized_code),
            min_optimize=min_optimize,
            # pyrefly: ignore [bad-argument-type]
            **compile_command,
        )
        optimized_build_option = CppTorchDeviceOptions(
            # pyrefly: ignore [bad-argument-type]
            compile_only=True,
            # pyrefly: ignore [bad-argument-type]
            **compile_command,
        )

        def get_hashable_command_line(build_option: BuildOptionsBase) -> str:
            """Writing the code to file will calculate a hash, which we need to vary if
            the command line flags change.  This implements a mostly-generic way of
            validating that."""
            return CppBuilder(
                name="o", sources="i", BuildOption=build_option
            ).get_command_line()

        main_cmd_line = get_hashable_command_line(main_build_option)
        optimized_cmd_line = get_hashable_command_line(optimized_build_option)

        key, main_path = write(
            main_code, "main.cpp", extra=f"{optimized_code} {main_cmd_line}"
        )

        # Don't bother writing if the argument is empty.
        if optimized_code:
            _, optimized_path = write(
                optimized_code, "optimized.cpp", extra=optimized_cmd_line
            )
        else:
            # Unused, but makes type checkers happy.
            optimized_path = os.devnull

        if key not in cls.cache:
            from torch.utils._filelock import FileLock

            lock_path = os.path.join(get_lock_dir(), key + ".lock")
            future: Future[Any] | None = None
            lib = None

            # if requested, pre-compile any headers
            if config.cpp_cache_precompile_headers and not _IS_WINDOWS:
                if header := cls._get_uncompiled_header(device_type):
                    main_build_option.precompiled_header = _precompile_header(
                        header,
                        main_cmd_line,
                        min_optimize=min_optimize,
                        **compile_command,
                    )

                # Currently, the optimized_code field is only used for cpp kernel code,
                # so go ahead and precompile the relevant header here.  Revisit this
                # decision if that ever changes.
                if optimized_code and (header := _get_cpp_prefix_header(device_type)):
                    optimized_build_option.precompiled_header = _precompile_header(
                        # pyrefly: ignore [unbound-name]
                        header,
                        optimized_cmd_line,
                        **compile_command,
                    )

            main_name, output_dir = get_name_and_dir_from_output_file_path(main_path)
            main_builder = CppBuilder(
                name=main_name,
                sources=main_path,
                BuildOption=main_build_option,
                output_dir=output_dir,
            )

            if optimized_code:
                optimized_name, _ = get_name_and_dir_from_output_file_path(
                    optimized_path
                )
                optimized_builder = CppBuilder(
                    name=optimized_name,
                    sources=optimized_path,
                    BuildOption=optimized_build_option,
                    output_dir=output_dir,
                )

                linker = CppBuilder(
                    name=main_name,
                    sources=[
                        main_builder.get_target_file_path(),
                        optimized_builder.get_target_file_path(),
                    ],
                    # pyrefly: ignore [bad-argument-type]
                    BuildOption=CppTorchDeviceOptions(**compile_command),
                    output_dir=output_dir,
                )

                worker_fn = functools.partial(
                    _worker_compile_cpp,
                    lock_path,
                    (main_builder, optimized_builder, linker),
                )
                binary_path = normalize_path_separator(linker.get_target_file_path())
            else:
                worker_fn = functools.partial(
                    _worker_compile_cpp, lock_path, (main_builder,)
                )
                binary_path = normalize_path_separator(
                    main_builder.get_target_file_path()
                )

            def load_fn() -> Any:
                nonlocal lib
                if lib is None:
                    if future is not None:
                        future.result()
                    result = worker_fn()
                    assert result is None
                    lib = cls._load_library(binary_path, key)
                    assert lib is not None
                return lib

            if submit_fn is not None:
                with FileLock(lock_path, timeout=LOCK_TIMEOUT):
                    if not os.path.exists(binary_path):
                        future = submit_fn(worker_fn)

            cls.cache[key] = load_fn

        return cls.cache[key]