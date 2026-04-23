def find_device_library(cls) -> str:
        """
        Find the path to the NVSHMEM device library.

        Returns:
            str: The path to libnvshmem_device.bc (included).
        """
        if cls.found_device_lib_path is not None:
            # Return the cached path if it exists
            return cls.found_device_lib_path

        # First, check if the user has specified a custom library path
        user_lib_dir = os.environ.get("NVSHMEM_LIB_DIR", None)
        if user_lib_dir is not None:
            lib_path = os.path.join(user_lib_dir, "libnvshmem_device.bc")
            if not os.path.exists(lib_path):
                raise RuntimeError(
                    f"NVSHMEM device library not found at specified path: {user_lib_dir}"
                )
            cls.found_device_lib_path = lib_path
            return lib_path

        # Otherwise, search for the library in the default installation paths
        paths = [
            os.path.join(sysconfig.get_path("purelib"), "nvidia", "nvshmem", "lib")
        ]

        # Add common system installation paths
        common_paths = [
            "/usr/local/lib",
            "/usr/lib",
            "/opt/nvidia/nvshmem/lib",
        ]
        paths.extend(common_paths)

        try:
            import torch

            torch_lib = os.path.join(os.path.dirname(torch.__file__), "lib")
            so_path = os.path.join(torch_lib, "libtorch_nvshmem.so")

            if os.path.exists(so_path):
                try:
                    result = subprocess.run(
                        ["readelf", "-d", so_path],
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    for line in result.stdout.splitlines():
                        if ("RPATH" in line or "RUNPATH" in line) and "[" in line:
                            rpath = line.split("[", 1)[1].split("]", 1)[0]
                            for p in rpath.split(":"):
                                p = p.strip().replace("$ORIGIN", torch_lib)
                                if p and p not in paths:
                                    paths.append(p)
                except subprocess.CalledProcessError:
                    pass

        except ImportError:
            pass

        for path in paths:
            device_lib = os.path.join(path, "libnvshmem_device.bc")
            if os.path.exists(device_lib):
                cls.found_device_lib_path = device_lib
                return device_lib

        raise RuntimeError(f"NVSHMEM device library not found. Searched: {paths}")