def validate_server(
    server_path: Path,
    probe_path: Path,
    host: HostInfo,
    install_dir: Path,
    *,
    runtime_line: str | None = None,
    install_kind: str | None = None,
) -> None:
    last_failure: PrebuiltFallback | None = None
    for port_attempt in range(1, SERVER_PORT_BIND_ATTEMPTS + 1):
        port = free_local_port()
        command = [
            str(server_path),
            "-m",
            str(probe_path),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "-c",
            "32",
            "--parallel",
            "1",
            "--threads",
            "1",
            "--ubatch-size",
            "32",
            "--batch-size",
            "32",
        ]
        # Only enable GPU offload for assets that actually ship GPU code.
        # Gating on `host.has_rocm` alone breaks the intentional CPU
        # fallback on AMD Windows hosts without a HIP prebuilt: the CPU
        # binary would be launched with `--n-gpu-layers 1` and fail
        # validation. Use the resolved install_kind as the source of
        # truth and fall back to host detection when the caller did not
        # pass one (keeps backwards compatibility with older call sites).
        _gpu_kinds = {
            "linux-cuda",
            "linux-rocm",
            "windows-cuda",
            "windows-hip",
            "macos-arm64",
        }
        if install_kind is not None:
            _enable_gpu_layers = install_kind in _gpu_kinds
        else:
            # Older call sites that don't pass install_kind: keep ROCm
            # hosts in the GPU-validation path so an AMD-only Linux host
            # is exercised against the actual hardware rather than the
            # CPU fallback. NVIDIA and macOS-arm64 are already covered.
            _enable_gpu_layers = (
                host.has_usable_nvidia
                or host.has_rocm
                or (host.is_macos and host.is_arm64)
            )
        if _enable_gpu_layers:
            command.extend(["--n-gpu-layers", "1"])

        log_fd, log_name = tempfile.mkstemp(prefix = "llama-server-", suffix = ".log")
        os.close(log_fd)
        log_path = Path(log_name)
        process: subprocess.Popen[str] | None = None
        try:
            with log_path.open("w", encoding = "utf-8", errors = "replace") as log_handle:
                process = subprocess.Popen(
                    command,
                    stdout = log_handle,
                    stderr = subprocess.STDOUT,
                    text = True,
                    env = binary_env(
                        server_path, install_dir, host, runtime_line = runtime_line
                    ),
                )
                deadline = time.time() + 20
                startup_started = time.time()
                response_body = ""
                last_error: Exception | None = None
                while time.time() < deadline:
                    if process.poll() is not None:
                        process.wait(timeout = 5)
                        log_handle.flush()
                        output = read_log_excerpt(log_path)
                        exited_quickly = (
                            time.time() - startup_started
                        ) <= SERVER_BIND_RETRY_WINDOW_SECONDS
                        failure = PrebuiltFallback(
                            "llama-server exited during startup:\n" + output
                        )
                        if (
                            port_attempt < SERVER_PORT_BIND_ATTEMPTS
                            and is_retryable_server_bind_error(
                                last_error,
                                output,
                                exited_quickly = exited_quickly,
                            )
                        ):
                            log(
                                f"llama-server startup hit a port race on {port}; retrying with a fresh port "
                                f"({port_attempt}/{SERVER_PORT_BIND_ATTEMPTS})"
                            )
                            last_failure = failure
                            break
                        raise failure

                    payload = json.dumps({"prompt": "a", "n_predict": 1}).encode(
                        "utf-8"
                    )
                    request = urllib.request.Request(
                        f"http://127.0.0.1:{port}/completion",
                        data = payload,
                        headers = {"Content-Type": "application/json"},
                    )
                    try:
                        with urllib.request.urlopen(request, timeout = 5) as response:
                            status_code = response.status
                            response_body = response.read().decode("utf-8", "replace")
                            if status_code == 200:
                                return
                            last_error = RuntimeError(
                                f"unexpected HTTP status {status_code}"
                            )
                    except urllib.error.HTTPError as exc:
                        response_body = exc.read().decode("utf-8", "replace")
                        last_error = exc
                    except Exception as exc:
                        last_error = exc
                    time.sleep(0.5)
                else:
                    log_handle.flush()
                    output = read_log_excerpt(log_path)
                    raise PrebuiltFallback(
                        "llama-server completion validation timed out"
                        + (f" ({last_error})" if last_error else "")
                        + ":\n"
                        + output
                        + ("\n" + response_body if response_body else "")
                    )
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout = 5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout = 5)
            try:
                log_path.unlink(missing_ok = True)
            except Exception:
                pass
    if last_failure is not None:
        raise last_failure
    raise PrebuiltFallback("llama-server validation failed unexpectedly")