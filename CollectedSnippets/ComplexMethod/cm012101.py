def build_standalone_runtime(cls) -> str:
        if cls._standalone_runtime_path and os.path.exists(
            cls._standalone_runtime_path
        ):
            return cls._standalone_runtime_path
        device_type = "cuda" if torch.cuda.is_available() else "cpu"
        libname = "libStandaloneHalideRuntime.so"
        target = "host-cuda" if device_type == "cuda" else "host"
        if cls._standalone_runtime_path:
            assert not os.path.exists(cls._standalone_runtime_path)
            # We hit this case in unittests when we run with fresh_cache()
            # Generating a fresh runtime over and over causes errors because we initialize
            # cuda hundreds of times in the same process and run out of file descriptors.
            # Workaround by jail breaking the current fresh_cache().
            base = default_cache_dir()
        else:
            base = cache_dir()
        dirpath = Path(base) / f"halide-runtime-{target}-{cls.config_hash()}"
        os.makedirs(dirpath, exist_ok=True)
        done_file = str(dirpath / "done")
        lock_file = str(dirpath / "lock")
        hook_file = str(dirpath / "hooks.cpp")
        a_file = str(dirpath / "standalone_halide_runtime.a")
        so_file = str(dirpath / libname)
        if not os.path.exists(done_file):
            import halide as hl  # type: ignore[import-untyped,import-not-found]

            from torch.utils._filelock import FileLock

            with FileLock(lock_file, LOCK_TIMEOUT):
                if not os.path.exists(done_file):
                    with open(hook_file, "w") as f:
                        if device_type == "cuda":
                            f.write(
                                cls.standalone_runtime_cuda_init.format(
                                    cls.find_header("HalideRuntimeCuda.h")
                                )
                            )
                    hl.compile_standalone_runtime(a_file, hl.Target(target))

                    name, output_dir = get_name_and_dir_from_output_file_path(so_file)
                    halide_cmd_gen = CppBuilder(
                        name=name,
                        sources=[hook_file, a_file],
                        output_dir=output_dir,
                        BuildOption=CppTorchDeviceOptions(
                            device_type=device_type,
                        ),
                    )

                    subprocess.check_call(
                        shlex.split(halide_cmd_gen.get_command_line())
                    )
                    touch(done_file)
        assert os.path.exists(so_file)
        cls._standalone_runtime_path = so_file
        return so_file