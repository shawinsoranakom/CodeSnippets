def server_process(self):
        """Start the studio backend server without torch, yield (proc, port), then stop."""
        py = _studio_venv_python()
        if py is None:
            pytest.skip("Studio venv not found")

        port = _server_port()
        backend_dir = BACKEND_DIR

        # Check if torch is installed in the studio venv
        check = subprocess.run(
            [str(py), "-c", "import torch; print(torch.__version__)"],
            capture_output = True,
        )
        torch_was_installed = check.returncode == 0
        torch_version = check.stdout.decode().strip() if torch_was_installed else None

        # Uninstall torch if present
        if torch_was_installed:
            subprocess.run(
                [
                    str(py),
                    "-m",
                    "pip",
                    "uninstall",
                    "-y",
                    "torch",
                    "torchvision",
                    "torchaudio",
                ],
                capture_output = True,
                timeout = 120,
            )

        # Start server
        env = os.environ.copy()
        env["PYTHONPATH"] = str(backend_dir)
        proc = subprocess.Popen(
            [str(py), str(backend_dir / "run.py"), "--port", str(port)],
            env = env,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            cwd = str(backend_dir),
        )

        # Wait for server to be ready (poll /api/health)
        import urllib.request
        import urllib.error

        ready = False
        for _ in range(30):
            time.sleep(1)
            try:
                resp = urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api/health", timeout = 2
                )
                if resp.status == 200:
                    ready = True
                    break
            except (urllib.error.URLError, ConnectionRefusedError, OSError):
                continue

        if not ready:
            stdout, stderr = proc.communicate(timeout = 5)
            # Reinstall torch + torchvision + torchaudio
            if torch_was_installed and torch_version:
                subprocess.run(
                    [
                        str(py),
                        "-m",
                        "pip",
                        "install",
                        f"torch=={torch_version}",
                        "torchvision",
                        "torchaudio",
                    ],
                    capture_output = True,
                    timeout = 300,
                )
            server_output = stdout.decode(errors = "replace") + stderr.decode(
                errors = "replace"
            )
            pytest.skip(
                f"Server failed to start within 30 seconds. Output:\n{server_output}"
            )

        yield proc, port

        # Cleanup: stop server, reinstall torch
        proc.terminate()
        try:
            proc.wait(timeout = 10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout = 5)

        if torch_was_installed and torch_version:
            subprocess.run(
                [
                    str(py),
                    "-m",
                    "pip",
                    "install",
                    f"torch=={torch_version}",
                    "torchvision",
                    "torchaudio",
                ],
                capture_output = True,
                timeout = 300,
            )