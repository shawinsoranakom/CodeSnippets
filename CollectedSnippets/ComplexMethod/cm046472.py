def windows_runtime_dirs() -> list[str]:
    candidates: list[str | Path] = []

    env_dirs = os.environ.get("CUDA_RUNTIME_DLL_DIR", "")
    if env_dirs:
        candidates.extend(part for part in env_dirs.split(os.pathsep) if part)

    path_dirs = os.environ.get("PATH", "")
    if path_dirs:
        candidates.extend(part for part in path_dirs.split(os.pathsep) if part)

    cuda_roots: list[Path] = []
    for name in ("CUDA_PATH", "CUDA_HOME", "CUDA_ROOT"):
        value = os.environ.get(name)
        if value:
            cuda_roots.append(Path(value))

    for root in cuda_roots:
        candidates.extend([root / "bin", root / "lib" / "x64"])

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    toolkit_base = Path(program_files) / "NVIDIA GPU Computing Toolkit" / "CUDA"
    if toolkit_base.is_dir():
        candidates.extend(toolkit_base.glob("v*/bin"))
        candidates.extend(toolkit_base.glob("v*/lib/x64"))

    candidates.extend(Path(path) for path in python_runtime_dirs())
    return dedupe_existing_dirs(candidates)