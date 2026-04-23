def add_lib_preload(self, lib_type):
        """Enable TCMalloc/JeMalloc/intel OpenMP."""
        library_paths = []
        if "CONDA_PREFIX" in os.environ:
            library_paths.append(f"{os.environ['CONDA_PREFIX']}/lib")
        if "VIRTUAL_ENV" in os.environ:
            library_paths.append(f"{os.environ['VIRTUAL_ENV']}/lib")

        library_paths += [
            f"{expanduser('~')}/.local/lib",
            "/usr/local/lib",
            "/usr/local/lib64",
            "/usr/lib",
            "/usr/lib64",
        ]

        lib_find = False
        lib_set = False
        for item in os.getenv("LD_PRELOAD", "").split(":"):
            if item.endswith(f"lib{lib_type}.so"):
                lib_set = True
                break
        if not lib_set:
            for lib_path in library_paths:
                # pyrefly: ignore [unbound-name]
                library_file = os.path.join(lib_path, f"lib{lib_type}.so")
                matches = glob.glob(library_file)
                if len(matches) > 0:
                    # pyrefly: ignore [unbound-name]
                    ld_preloads = [f"{matches[0]}", os.getenv("LD_PRELOAD", "")]
                    # pyrefly: ignore [unbound-name]
                    os.environ["LD_PRELOAD"] = os.pathsep.join(
                        # pyrefly: ignore [unbound-name]
                        [p.strip(os.pathsep) for p in ld_preloads if p]
                    )
                    lib_find = True
                    break
        return lib_set or lib_find