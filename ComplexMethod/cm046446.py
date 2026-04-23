def detected_linux_runtime_lines() -> tuple[list[str], dict[str, list[str]]]:
    line_requirements = {
        "cuda13": ["libcudart.so.13", "libcublas.so.13"],
        "cuda12": ["libcudart.so.12", "libcublas.so.12"],
    }
    detected: list[str] = []
    runtime_dirs: dict[str, list[str]] = {}
    for line, required in line_requirements.items():
        dirs = linux_runtime_dirs_for_required_libraries(required)
        library_matches: dict[str, list[str]] = {}
        matching_dirs: list[str] = []
        for library in required:
            matched_dirs = [
                directory
                for directory in dirs
                if any(Path(directory).glob(f"{library}*"))
            ]
            if not matched_dirs:
                library_matches = {}
                matching_dirs = []
                break
            library_matches[library] = matched_dirs
            for directory in matched_dirs:
                if directory not in matching_dirs:
                    matching_dirs.append(directory)
        if library_matches:
            detected.append(line)
            runtime_dirs[line] = matching_dirs
    return detected, runtime_dirs