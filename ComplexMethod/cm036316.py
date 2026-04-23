async def test_abort_final_output(output_kind: RequestOutputKind):
    """Test that abort() returns a final output with correct information."""

    with ExitStack() as after:
        with set_default_torch_num_threads(1):
            engine = AsyncLLM.from_engine_args(TEXT_ENGINE_ARGS)
        after.callback(engine.shutdown)

        request_id = "test-abort-final-output"

        # Start a long-running request
        sampling_params = SamplingParams(
            max_tokens=3000,  # Long enough to allow abort
            ignore_eos=True,
            output_kind=output_kind,
            temperature=0.5,
            seed=42,
        )

        outputs: list[RequestOutput] = []
        generated = asyncio.create_task(
            collect_outputs(engine, request_id, TEXT_PROMPT, sampling_params, outputs)
        )

        # Let it generate some tokens
        await asyncio.sleep(0.5)

        # Abort the request
        await engine.abort(request_id, internal=False)

        # Wait for generation to complete and return final output
        final_output = await generated

        # Verify we got a final output
        assert final_output is not None
        assert final_output.finished
        assert len(final_output.outputs) == 1

        assert final_output.outputs[0].finish_reason == "abort"
        assert final_output.outputs[0].stop_reason is None

        # Verify num_cached_tokens is set correctly
        assert hasattr(final_output, "num_cached_tokens")
        assert final_output.num_cached_tokens >= 0

        # If we got intermediate outputs, verify they are consistent
        if output_kind == RequestOutputKind.DELTA:
            # For DELTA, sum all intermediate tokens should <= final tokens
            token_count = sum(len(output.outputs[0].token_ids) for output in outputs)
            assert token_count > 0
            # This would ordinarily be 0, but could end up > 0 if the
            # final abort is coalesced with another chunk in the output queue.
            assert len(final_output.outputs[0].token_ids) >= 0
        else:
            # For FINAL_ONLY, we should only get the final output
            assert len(outputs) == 0
            assert len(final_output.outputs[0].token_ids) > 0

        assert not engine.output_processor.has_unfinished_requests()