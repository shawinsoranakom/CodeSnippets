def test_serve_starts_server_no_asyncio_error(self, simple_agent_flow_path: Path):
        """Regression test: lfx serve should not fail with asyncio error.

        This test verifies the fix for the issue where lfx serve failed with:
        'asyncio.run() cannot be called from a running event loop'

        The fix was to use uvicorn.Server with await server.serve() instead of
        uvicorn.run() which internally calls asyncio.run().
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            test_port = s.getsockname()[1]

        # Start serve in a subprocess with unbuffered output on a specific port
        proc = subprocess.Popen(  # noqa: S603
            [
                sys.executable,
                "-u",  # Unbuffered output
                "-m",
                "lfx",
                "serve",
                "--verbose",
                "--port",
                str(test_port),
                str(simple_agent_flow_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ, "LANGFLOW_API_KEY": "test-key-12345"},  # pragma: allowlist secret
        )

        server_ready = False
        output_chunks = []
        timeout = 15  # seconds
        start_time = time.time()
        actual_port = test_port

        try:
            while time.time() - start_time < timeout:
                # Check if process exited
                exit_code = proc.poll()
                if exit_code is not None:
                    # Process exited - read remaining output
                    if proc.stdout:
                        remaining = proc.stdout.read()
                        if remaining:
                            output_chunks.append(remaining)
                    output = "".join(output_chunks)

                    # Check for the specific asyncio errors we're regression testing
                    if "asyncio.run() cannot be called from a running event loop" in output:
                        pytest.fail(f"Regression: lfx serve failed with asyncio error.\nOutput:\n{output}")

                    if "coroutine 'Server.serve' was never awaited" in output:
                        pytest.fail(f"Regression: Server.serve coroutine was never awaited.\nOutput:\n{output}")

                    # Process exited for another reason
                    pytest.fail(f"Server process exited with code {exit_code}.\nOutput:\n{output}")

                # Try to read available output without blocking (Unix only)
                if proc.stdout:
                    try:
                        ready, _, _ = select.select([proc.stdout], [], [], 0.1)
                        if ready:
                            chunk = proc.stdout.readline()
                            if chunk:
                                output_chunks.append(chunk)
                                # Check if server switched to a different port
                                if "using port" in chunk.lower():
                                    port_match = re.search(r"port (\d+)", chunk)
                                    if port_match:
                                        actual_port = int(port_match.group(1))
                    except (ValueError, OSError):
                        pass

                # Try to connect to server on actual port
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{actual_port}/docs", timeout=1)
                    server_ready = True
                    break
                except Exception:
                    time.sleep(0.3)

            if not server_ready:
                output = "".join(output_chunks)
                pytest.fail(f"Server did not become ready within {timeout}s.\nOutput:\n{output}")

        finally:
            # Clean up - terminate the server
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()