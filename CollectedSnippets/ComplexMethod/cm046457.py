def detect_torch_cuda_runtime_preference(host: HostInfo) -> CudaRuntimePreference:
    selection_log: list[str] = []
    if host.is_macos:
        selection_log.append("torch_cuda_preference: skipped on macOS")
        return CudaRuntimePreference(runtime_line = None, selection_log = selection_log)
    if not (host.has_usable_nvidia and (host.is_linux or host.is_windows)):
        selection_log.append(
            "torch_cuda_preference: skipped because CUDA host prerequisites were not met"
        )
        return CudaRuntimePreference(runtime_line = None, selection_log = selection_log)

    try:
        import torch
    except Exception as exc:
        selection_log.append(f"torch_cuda_preference: import failed: {exc}")
        return CudaRuntimePreference(runtime_line = None, selection_log = selection_log)

    cuda_version = getattr(getattr(torch, "version", None), "cuda", None)
    if not isinstance(cuda_version, str) or not cuda_version.strip():
        selection_log.append(
            "torch_cuda_preference: torch.version.cuda missing; skipping Torch shortcut"
        )
        return CudaRuntimePreference(runtime_line = None, selection_log = selection_log)

    try:
        cuda_available = bool(torch.cuda.is_available())
    except Exception as exc:
        selection_log.append(
            f"torch_cuda_preference: torch.cuda.is_available() failed: {exc}"
        )
        return CudaRuntimePreference(runtime_line = None, selection_log = selection_log)

    if not cuda_available:
        selection_log.append(
            "torch_cuda_preference: torch.cuda.is_available() returned False; falling back to normal selection"
        )
        return CudaRuntimePreference(runtime_line = None, selection_log = selection_log)

    runtime_line = runtime_line_from_cuda_version(cuda_version)
    if runtime_line is None:
        selection_log.append(
            f"torch_cuda_preference: unsupported torch.version.cuda={cuda_version}; falling back to normal selection"
        )
        return CudaRuntimePreference(runtime_line = None, selection_log = selection_log)

    selection_log.append(
        "torch_cuda_preference: selected runtime_line="
        f"{runtime_line} from torch.version.cuda={cuda_version}"
    )
    return CudaRuntimePreference(runtime_line = runtime_line, selection_log = selection_log)