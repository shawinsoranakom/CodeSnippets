def linux_runtime_dirs_for_required_libraries(
    required_libraries: Iterable[str],
) -> list[str]:
    required = [library for library in required_libraries if library]
    candidates: list[str | Path] = []

    env_dirs = os.environ.get("CUDA_RUNTIME_LIB_DIR", "")
    if env_dirs:
        candidates.extend(part for part in env_dirs.split(os.pathsep) if part)
    ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
    if ld_library_path:
        candidates.extend(part for part in ld_library_path.split(os.pathsep) if part)

    cuda_roots: list[Path] = []
    for name in ("CUDA_HOME", "CUDA_PATH", "CUDA_ROOT"):
        value = os.environ.get(name)
        if value:
            cuda_roots.append(Path(value))
    cuda_roots.extend(
        Path(path) for path in glob_paths("/usr/local/cuda", "/usr/local/cuda-*")
    )

    for root in cuda_roots:
        candidates.extend(
            [
                root / "lib",
                root / "lib64",
                root / "targets" / "x86_64-linux" / "lib",
            ]
        )

    candidates.extend(
        Path(path)
        for path in glob_paths(
            "/lib",
            "/lib64",
            "/usr/lib",
            "/usr/lib64",
            "/usr/local/lib",
            "/usr/local/lib64",
            "/lib/x86_64-linux-gnu",
            "/usr/lib/x86_64-linux-gnu",
        )
    )
    candidates.extend(
        Path(path)
        for path in glob_paths("/usr/local/lib/ollama/cuda_v*", "/usr/lib/wsl/lib")
    )
    candidates.extend(Path(path) for path in python_runtime_dirs())
    candidates.extend(Path(path) for path in ldconfig_runtime_dirs(required))

    resolved = dedupe_existing_dirs(candidates)
    if not required:
        return resolved

    matched: list[tuple[int, str]] = []
    for directory in resolved:
        base = Path(directory)
        provided = sum(
            1 for library in required if dir_provides_exact_library(directory, library)
        )
        if provided:
            matched.append((provided, directory))

    matched.sort(key = lambda item: item[0], reverse = True)
    return [directory for _, directory in matched]