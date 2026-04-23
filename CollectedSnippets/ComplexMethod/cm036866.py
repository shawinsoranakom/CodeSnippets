async def test_mixed_delta_reasoning_and_content_emits_reasoning_delta(
        self, monkeypatch
    ):
        """When the reasoning parser produces a delta with both reasoning
        and content set (e.g. reasoning end and content start in the same
        chunk), the trailing reasoning text must be emitted as a
        ResponseReasoningTextDeltaEvent and included in the
        ResponseReasoningTextDoneEvent text."""

        monkeypatch.setattr(envs, "VLLM_USE_EXPERIMENTAL_PARSER_CONTEXT", False)
        serving = _make_serving_instance_with_reasoning()

        # Sequence of DeltaMessages the mock orchestrator will return
        delta_sequence = [
            DeltaMessage(reasoning="thinking..."),
            DeltaMessage(reasoning=" end", content="hello"),  # mixed delta
            DeltaMessage(content=" world"),
        ]
        _mock_parser_with_reasoning(serving, delta_sequence)
        # Create contexts for each streaming chunk
        contexts = [
            _make_simple_context_with_output("chunk1", [10]),
            _make_simple_context_with_output("chunk2", [20]),
            _make_simple_context_with_output("chunk3", [30]),
        ]

        async def result_generator():
            for ctx in contexts:
                yield ctx

        request = ResponsesRequest(input="hi", tools=[], stream=True)
        sampling_params = SamplingParams(max_tokens=64)
        metadata = RequestResponseMetadata(request_id="req")
        _identity_increment._counter = 0  # type: ignore

        events = []
        async for event in serving._process_simple_streaming_events(
            request=request,
            sampling_params=sampling_params,
            result_generator=result_generator(),
            context=SimpleContext(),
            model_name="test-model",
            tokenizer=MagicMock(),
            request_metadata=metadata,
            created_time=0,
            _increment_sequence_number_and_return=_identity_increment,
        ):
            events.append(event)

        # The first reasoning delta should be emitted
        reasoning_deltas = [
            e for e in events if isinstance(e, ResponseReasoningTextDeltaEvent)
        ]
        assert len(reasoning_deltas) == 2
        assert reasoning_deltas[0].delta == "thinking..."
        # The trailing reasoning from the mixed delta must also be emitted
        assert reasoning_deltas[1].delta == " end"

        # The done event must include both reasoning parts
        reasoning_done = [
            e for e in events if isinstance(e, ResponseReasoningTextDoneEvent)
        ]
        assert len(reasoning_done) == 1
        assert reasoning_done[0].text == "thinking... end"

        # Content deltas should be emitted for both the mixed delta's
        # content and the pure content delta
        text_deltas = [e for e in events if isinstance(e, ResponseTextDeltaEvent)]
        assert len(text_deltas) == 2
        assert text_deltas[0].delta == "hello"
        assert text_deltas[1].delta == " world"