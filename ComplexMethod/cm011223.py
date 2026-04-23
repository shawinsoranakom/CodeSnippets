def find_device_library(cls) -> str:
        if cls.found_device_lib_path is not None:
            return cls.found_device_lib_path

        if not torch.cuda.is_available():
            raise RuntimeError(
                "ROCm/CUDA not available — cannot detect GPU architecture"
            )

        props = torch.cuda.get_device_properties(0)
        # gcnArchName returns e.g. "gfx942:sramecc+:xnack-"
        arch = props.gcnArchName.split(":")[0]
        logger.info("Detected GPU architecture: %s", arch)

        lib_name = f"librocshmem_device_{arch}.bc"

        search_paths = [
            os.path.join(sysconfig.get_path("purelib"), "amd", "rocshmem", "lib"),
            "/opt/rocm/lib",
            "/usr/local/lib",
            "/usr/lib",
        ]

        user_lib_dir = os.environ.get("ROCSHMEM_LIB_DIR")
        if user_lib_dir is not None:
            lib_path = os.path.join(user_lib_dir, lib_name)
            if not os.path.exists(lib_path):
                raise RuntimeError(
                    f"rocSHMEM device library not found at ROCSHMEM_LIB_DIR: {lib_path}"
                )
            logger.info("Found rocSHMEM device library: %s", lib_path)
            cls.found_device_lib_path = lib_path
            return lib_path

        lib_path = None
        for path in search_paths:
            candidate = os.path.join(path, lib_name)
            if os.path.exists(candidate):
                lib_path = candidate
                break

        if lib_path is None:
            raise RuntimeError(
                f"rocSHMEM device library '{lib_name}' not found.\n"
                f"Searched: {search_paths}\n"
                "Set ROCSHMEM_LIB_DIR to the directory containing it."
            )
        logger.info("Found rocSHMEM device library: %s", lib_path)
        cls.found_device_lib_path = lib_path
        return lib_path