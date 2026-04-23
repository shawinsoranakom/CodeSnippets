def detect_host() -> HostInfo:
    system = platform.system()
    machine = platform.machine().lower()
    is_windows = system == "Windows"
    is_linux = system == "Linux"
    is_macos = system == "Darwin"
    is_x86_64 = machine in {"x86_64", "amd64"}
    is_arm64 = machine in {"arm64", "aarch64"}

    nvidia_smi = shutil.which("nvidia-smi")
    driver_cuda_version = None
    compute_caps: list[str] = []
    visible_cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    visible_device_tokens = parse_cuda_visible_devices(visible_cuda_devices)
    has_physical_nvidia = False
    has_usable_nvidia = False
    if nvidia_smi:
        # Require `nvidia-smi -L` to actually list a GPU before treating the
        # host as NVIDIA. The banner text "NVIDIA-SMI ..." is printed even
        # when the command fails to communicate with the driver (e.g. stale
        # container leftovers), which would otherwise misclassify an AMD
        # ROCm host as NVIDIA and short-circuit the ROCm path.
        try:
            listing = run_capture([nvidia_smi, "-L"], timeout = 20)
            gpu_lines = [
                line for line in listing.stdout.splitlines() if line.startswith("GPU ")
            ]
            if gpu_lines:
                has_physical_nvidia = True
                has_usable_nvidia = visible_device_tokens != []
        except Exception:
            pass

        try:
            result = run_capture([nvidia_smi], timeout = 20)
            merged = "\n".join(part for part in (result.stdout, result.stderr) if part)
            for line in merged.splitlines():
                if "CUDA Version:" in line:
                    raw = line.split("CUDA Version:", 1)[1].strip().split()[0]
                    major, minor = raw.split(".", 1)
                    driver_cuda_version = (int(major), int(minor))
                    break
        except Exception:
            pass

        try:
            caps = run_capture(
                [
                    nvidia_smi,
                    "--query-gpu=index,uuid,compute_cap",
                    "--format=csv,noheader",
                ],
                timeout = 20,
            )
            visible_gpu_rows: list[tuple[str, str, str]] = []
            for raw in caps.stdout.splitlines():
                parts = [part.strip() for part in raw.split(",")]
                if len(parts) != 3:
                    continue
                index, uuid, cap = parts
                visible_gpu_row = select_visible_gpu_rows(
                    [(index, uuid, cap)],
                    visible_device_tokens,
                )
                if not visible_gpu_row:
                    continue
                visible_gpu_rows.extend(visible_gpu_row)
                normalized_cap = normalize_compute_cap(cap)
                if normalized_cap is None:
                    continue
                if normalized_cap not in compute_caps:
                    compute_caps.append(normalized_cap)

            if visible_gpu_rows:
                has_usable_nvidia = True
                # Older nvidia-smi versions (pre -L support) hit the
                # except in the first try block but still succeed here,
                # leaving has_physical_nvidia unset. Mirror the -L path
                # so downstream diagnostics on line ~4390 still run.
                if not has_physical_nvidia:
                    has_physical_nvidia = True
            elif visible_device_tokens == []:
                has_usable_nvidia = False
            elif supports_explicit_visible_device_matching(visible_device_tokens):
                has_usable_nvidia = False
            elif has_physical_nvidia:
                has_usable_nvidia = True
        except Exception:
            pass

    # Detect AMD ROCm (HIP) -- require actual GPU, not just tools installed

    def _amd_smi_has_gpu(stdout: str) -> bool:
        """Check for 'GPU: <number>' data rows, not just a table header."""
        return bool(re.search(r"(?im)^gpu\s*[:\[]\s*\d", stdout))

    has_rocm = False
    if is_linux:
        for _cmd, _check in (
            # rocminfo: look for a real gfx GPU id (3-4 chars, nonzero first digit).
            # gfx000 is the CPU agent; ROCm 6.1+ also emits generic ISA lines like
            # "gfx11-generic" or "gfx9-4-generic" which only have 1-2 digits before
            # the dash and must not be treated as a real GPU.
            (
                ["rocminfo"],
                lambda out: bool(re.search(r"gfx[1-9][0-9a-z]{2,3}", out.lower())),
            ),
            (["amd-smi", "list"], _amd_smi_has_gpu),
        ):
            _exe = shutil.which(_cmd[0])
            if not _exe:
                continue
            try:
                _result = run_capture([_exe, *_cmd[1:]], timeout = 10)
            except Exception:
                continue
            if _result.returncode == 0 and _result.stdout.strip():
                if _check(_result.stdout):
                    has_rocm = True
                    break
    elif is_windows:
        # Windows: prefer active probes that validate GPU presence
        for _cmd, _check in (
            (["hipinfo"], lambda out: "gcnarchname" in out.lower()),
            (["amd-smi", "list"], _amd_smi_has_gpu),
        ):
            _exe = shutil.which(_cmd[0])
            if not _exe:
                continue
            try:
                _result = run_capture([_exe, *_cmd[1:]], timeout = 10)
            except Exception:
                continue
            if _result.returncode == 0 and _result.stdout.strip():
                if _check(_result.stdout):
                    has_rocm = True
                    break
        # Note: amdhip64.dll presence alone is NOT treated as GPU evidence
        # since the HIP SDK can be installed without an AMD GPU.

    return HostInfo(
        system = system,
        machine = machine,
        is_windows = is_windows,
        is_linux = is_linux,
        is_macos = is_macos,
        is_x86_64 = is_x86_64,
        is_arm64 = is_arm64,
        nvidia_smi = nvidia_smi,
        driver_cuda_version = driver_cuda_version,
        compute_caps = compute_caps,
        visible_cuda_devices = visible_cuda_devices,
        has_physical_nvidia = has_physical_nvidia,
        has_usable_nvidia = has_usable_nvidia,
        has_rocm = has_rocm,
    )