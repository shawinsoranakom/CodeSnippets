def binary_env(
    binary_path: Path,
    install_dir: Path,
    host: HostInfo,
    *,
    runtime_line: str | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    if host.is_windows:
        path_dirs = [
            str(binary_path.parent),
            *windows_runtime_dirs_for_runtime_line(runtime_line),
        ]
        existing = [part for part in env.get("PATH", "").split(os.pathsep) if part]
        env["PATH"] = os.pathsep.join(dedupe_existing_dirs([*path_dirs, *existing]))
    elif host.is_linux:
        ld_dirs = [
            str(binary_path.parent),
            str(install_dir),
            *linux_runtime_dirs(binary_path),
        ]
        existing = [
            part for part in env.get("LD_LIBRARY_PATH", "").split(os.pathsep) if part
        ]
        env["LD_LIBRARY_PATH"] = os.pathsep.join(
            dedupe_existing_dirs([*ld_dirs, *existing])
        )
    elif host.is_macos:
        dyld_dirs = [str(binary_path.parent), str(install_dir)]
        existing = [
            part for part in env.get("DYLD_LIBRARY_PATH", "").split(os.pathsep) if part
        ]
        env["DYLD_LIBRARY_PATH"] = os.pathsep.join(
            dedupe_existing_dirs([*dyld_dirs, *existing])
        )
    return env