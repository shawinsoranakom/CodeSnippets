def collect_system_report(
    host: HostInfo, choice: AssetChoice | None, install_dir: Path
) -> str:
    lines = [
        f"platform={host.system} machine={host.machine}",
        f"driver_cuda_version={host.driver_cuda_version}",
        f"compute_caps={','.join(host.compute_caps) if host.compute_caps else 'unknown'}",
        f"cuda_visible_devices={host.visible_cuda_devices if host.visible_cuda_devices is not None else 'unset'}",
        f"has_physical_nvidia={host.has_physical_nvidia}",
        f"has_usable_nvidia={host.has_usable_nvidia}",
        f"chosen_asset={(choice.name if choice else 'none')}",
        f"asset_source={(choice.source_label if choice else 'none')}",
    ]
    if host.is_linux and host.has_physical_nvidia:
        runtime_lines, runtime_dirs = detected_linux_runtime_lines()
        lines.append(
            "linux_runtime_lines="
            + (",".join(runtime_lines) if runtime_lines else "none")
        )
        for runtime_line in ("cuda13", "cuda12"):
            lines.append(
                f"linux_runtime_dirs_{runtime_line}="
                + (
                    ",".join(runtime_dirs.get(runtime_line, []))
                    if runtime_dirs.get(runtime_line)
                    else "none"
                )
            )
    if choice and choice.selection_log:
        lines.append("selection_log:")
        lines.extend(choice.selection_log)
    if host.nvidia_smi:
        try:
            smi = run_capture([host.nvidia_smi], timeout = 20)
            excerpt = "\n".join((smi.stdout + smi.stderr).splitlines()[:20])
            lines.append("nvidia-smi:")
            lines.append(excerpt)
        except Exception as exc:
            lines.append(f"nvidia-smi error: {exc}")

    if host.is_linux:
        server_binary = install_dir / "llama-server"
        if server_binary.exists():
            server_env = binary_env(server_binary, install_dir, host)
            lines.append(
                "linux_missing_libs="
                + (
                    ",".join(linux_missing_libraries(server_binary, env = server_env))
                    or "none"
                )
            )
            lines.append(
                "linux_runtime_dirs="
                + (
                    ",".join(
                        [
                            part
                            for part in server_env.get("LD_LIBRARY_PATH", "").split(
                                os.pathsep
                            )
                            if part
                        ]
                    )
                    or "none"
                )
            )
            try:
                ldd = run_capture(
                    ["ldd", str(server_binary)], timeout = 20, env = server_env
                )
                lines.append("ldd llama-server:")
                lines.append((ldd.stdout + ldd.stderr).strip())
            except Exception as exc:
                lines.append(f"ldd error: {exc}")
    elif host.is_windows:
        lines.append(
            "windows_runtime_dirs=" + (",".join(windows_runtime_dirs()) or "none")
        )
        runtime_lines, runtime_dirs = detected_windows_runtime_lines()
        lines.append(
            "windows_runtime_lines="
            + (",".join(runtime_lines) if runtime_lines else "none")
        )
        for runtime_line in ("cuda13", "cuda12"):
            lines.append(
                f"windows_runtime_dirs_{runtime_line}="
                + (
                    ",".join(runtime_dirs.get(runtime_line, []))
                    if runtime_dirs.get(runtime_line)
                    else "none"
                )
            )
    elif host.is_macos:
        server_binary = install_dir / "llama-server"
        if server_binary.exists():
            try:
                otool = run_capture(["otool", "-L", str(server_binary)], timeout = 20)
                lines.append("otool -L llama-server:")
                lines.append((otool.stdout + otool.stderr).strip())
            except Exception as exc:
                lines.append(f"otool error: {exc}")

    return "\n".join(lines)