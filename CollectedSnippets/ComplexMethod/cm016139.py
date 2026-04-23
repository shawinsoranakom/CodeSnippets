def config_to_command(
    config: str,
    suite: str,
    model: str | None = None,
) -> str | None:
    """Turn a config name into a runnable benchmark command."""
    m = CONFIG_RE.match(config)
    if not m:
        return None

    backend_variant = m.group("backend")
    dtype = m.group("dtype")
    mode = m.group("mode")
    runtime = m.group("device")

    # Runtime → --device flag (strip platform suffix like _x86_zen)
    device_flag = runtime.split("_")[0]  # "cpu_x86_zen" → "cpu"

    cmd_parts = [
        "python",
        f"benchmarks/dynamo/{suite}.py",
        f"--{mode}",
        f"--{dtype}",
        "--backend",
        "inductor",
        "--device",
        device_flag,
    ]

    if "no_cudagraphs" in backend_variant:
        cmd_parts.append("--disable-cudagraphs")
    if "dynamic" in backend_variant:
        cmd_parts.extend(["--dynamic-shapes", "--dynamic-batch-only"])
    if "cpp_wrapper" in backend_variant:
        cmd_parts.insert(0, "TORCHINDUCTOR_CPP_WRAPPER=1")
        cmd_parts.append("--disable-cudagraphs")
    if "freezing" in backend_variant:
        cmd_parts.append("--freezing")
    if "max_autotune" in backend_variant:
        cmd_parts.insert(0, "TORCHINDUCTOR_MAX_AUTOTUNE=1")
    if "aot_inductor" in backend_variant:
        cmd_parts.append("--export-aot-inductor")
        cmd_parts.append("--disable-cudagraphs")

    cmd_parts.extend(["--performance", "--cold-start-latency"])

    if model:
        cmd_parts.extend(["--only", model])

    cmd_parts.extend(["--output", f"{config}_performance.csv"])

    return " ".join(cmd_parts)