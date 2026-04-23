async def test_abort_during_final_step(async_scheduling: bool):
    """
    Test that a request aborted during its final execution step is treated as
    aborted rather than completed.

    This test:
    1. Monkeypatches execute_model to wait for a file to be deleted
    2. Configures a dummy KV connector to capture finish statuses
    3. Starts a request with max_tokens=1 (will complete on first decode step)
    4. Aborts the request, then deletes the file to unblock execute_model
    5. Verifies the KV connector received FINISHED_ABORTED not FINISHED_LENGTH_CAPPED

    See https://github.com/vllm-project/vllm/pull/29987.

    Without the fix, the KV connector would see FINISHED_LENGTH_CAPPED because
    update_from_output() would mark the request as completed before processing
    the abort. This causes KV cache blocks to not be freed properly in
    disaggregated prefill scenarios.

    With the fix, _process_aborts_queue() runs before update_from_output(), so the
    abort takes precedence and the KV connector sees FINISHED_ABORTED.
    """

    # Create three temporary files:
    # 1. ready_file: deleted by execute_model to signal it has started
    # 2. block_file: execute_model waits for this to be deleted
    # 3. status_file: KV connector writes finish statuses here
    with tempfile.NamedTemporaryFile(delete=False) as f:
        ready_file = Path(f.name)
    with tempfile.NamedTemporaryFile(delete=False) as f2:
        block_file = Path(f2.name)
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as f3:
        status_file = Path(f3.name)

    try:
        # Get the original execute_model method
        from vllm.v1.worker.gpu_worker import Worker

        original_execute_model = Worker.execute_model

        def execute_model_with_wait(self, scheduler_output):
            # Signal that execute_model has been called by deleting ready_file
            if ready_file.exists():
                ready_file.unlink()

            # Wait for the block file to be deleted (triggered from test after abort)
            # This runs in the worker process (after fork), so we poll the filesystem
            while block_file.exists():
                time.sleep(0.01)
            return original_execute_model(self, scheduler_output)

        # Patch execute_model to inject the wait
        # This happens before the worker process is forked, so the patch applies there
        with patch.object(Worker, "execute_model", execute_model_with_wait):
            request_id = "test-abort-final-step"

            # Configure engine with dummy KV connector
            # Pass the status file path so the connector can write to it
            kv_transfer_config = KVTransferConfig(
                kv_connector="DummyKVConnector",
                kv_role="kv_both",
                kv_connector_extra_config={"status_file": str(status_file)},
            )
            engine_args = AsyncEngineArgs(
                model="meta-llama/Llama-3.2-1B-Instruct",
                enforce_eager=True,
                async_scheduling=async_scheduling,
                kv_transfer_config=kv_transfer_config,
            )

            with set_default_torch_num_threads(1):
                engine = AsyncLLM.from_engine_args(engine_args)

            try:
                # Create a request that will complete after just 1 token
                sampling_params = SamplingParams(
                    max_tokens=1,
                    ignore_eos=True,
                    output_kind=RequestOutputKind.DELTA,
                )

                # Start generation in a task
                outputs = []

                async def generate():
                    async for output in engine.generate(
                        request_id=request_id,
                        prompt=TEXT_PROMPT,
                        sampling_params=sampling_params,
                    ):
                        outputs.append(output)

                gen_task = asyncio.create_task(generate())

                # Wait for execute_model to signal it has started (with timeout)
                timeout = 5.0  # 5 second timeout
                start_time = time.time()
                while ready_file.exists():
                    if time.time() - start_time > timeout:
                        raise TimeoutError(
                            "Timeout waiting for execute_model to start. "
                            "The monkeypatch may not be working correctly, "
                            "for example if spawn was used instead of fork."
                        )
                    await asyncio.sleep(0.01)

                # Abort the request while execute_model is blocked
                await engine.abort(request_id)

                # Now unblock execute_model by deleting the file
                # The abort should be processed before the model output
                block_file.unlink()

                # Wait for generation to complete
                await gen_task

                # Poll for the KV connector to record the finish status
                timeout = 5.0
                start = time.time()
                captured_statuses = []
                while time.time() - start < timeout:
                    with open(status_file) as f4:
                        status_lines = f4.read().strip().split("\n")
                        captured_statuses = [
                            line
                            for line in status_lines
                            if line and line.startswith("FINISHED_")
                        ]
                    if captured_statuses:
                        break
                    await asyncio.sleep(0.05)
                else:
                    raise TimeoutError(
                        "Timeout waiting for KV connector to record finish status."
                    )

                # Verify we got output
                assert len(outputs) > 0, "Should have received at least one output"

                # The final output should have finish_reason="abort"
                final_output = outputs[-1]
                assert final_output.finished, (
                    "Final output should be marked as finished"
                )
                assert final_output.outputs[0].finish_reason == "abort", (
                    f"Expected finish_reason='abort' but got "
                    f"'{final_output.outputs[0].finish_reason}'. "
                )

                assert len(captured_statuses) >= 1, (
                    f"Expected at least 1 captured finish status, got "
                    f"{len(captured_statuses)}. File content: {status_lines}"
                )

                assert "FINISHED_ABORTED" in captured_statuses, (
                    f"KV connector should see FINISHED_ABORTED but got "
                    f"{captured_statuses}. "
                )

                # Verify cleanup
                assert not engine.output_processor.has_unfinished_requests()

            finally:
                # Shutdown the engine
                engine.shutdown()

    finally:
        # Clean up temporary files if they still exist
        if ready_file.exists():
            ready_file.unlink()
        if block_file.exists():
            block_file.unlink()
        if status_file.exists():
            status_file.unlink()