def preflight_linux_installed_binaries(
    binaries: Iterable[Path],
    install_dir: Path,
    host: HostInfo,
) -> None:
    if not host.is_linux:
        return

    issues: list[str] = []
    for binary_path in binaries:
        env = binary_env(binary_path, install_dir, host)
        missing = linux_missing_libraries(binary_path, env = env)
        if not missing:
            continue
        runtime_dirs = [
            part for part in env.get("LD_LIBRARY_PATH", "").split(os.pathsep) if part
        ]
        issues.append(
            f"{binary_path.name}: missing={','.join(missing)} "
            f"ld_library_path={','.join(runtime_dirs) if runtime_dirs else 'none'}"
        )

    if issues:
        raise PrebuiltFallback(
            "linux extracted binary preflight failed:\n" + "\n".join(issues)
        )