async def test_abort_timeout_exits_quickly(wait_for_engine_idle: float):
    server_args = [
        "--dtype",
        "bfloat16",
        "--max-model-len",
        "256",
        "--enforce-eager",
        "--gpu-memory-utilization",
        "0.05",
        "--max-num-seqs",
        "4",
        "--shutdown-timeout",
        "0",
    ]

    with RemoteOpenAIServer(MODEL_NAME, server_args) as remote_server:
        proc = remote_server.proc
        child_pids = _get_child_pids(proc.pid)

        if wait_for_engine_idle > 0:
            client = remote_server.get_async_client()
            # Send requests to ensure engine is fully initialized
            for _ in range(2):
                await client.completions.create(
                    model=MODEL_NAME,
                    prompt="Test request: ",
                    max_tokens=10,
                )
            # Wait for engine to become idle
            await asyncio.sleep(wait_for_engine_idle)

        start_time = time.time()
        proc.send_signal(signal.SIGTERM)

        # abort timeout (0) should exit promptly
        for _ in range(20):
            if proc.poll() is not None:
                break
            time.sleep(0.1)

        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
            pytest.fail("Process did not exit after SIGTERM with abort timeout")

        exit_time = time.time() - start_time
        assert exit_time < 2, f"Default shutdown took too long: {exit_time:.1f}s"
        assert proc.returncode in (0, -15, None), f"Unexpected: {proc.returncode}"

        await _assert_children_cleaned_up(child_pids)