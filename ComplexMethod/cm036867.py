async def test_transition_without_mixed_delta_no_extra_reasoning_event(
        self, monkeypatch
    ):
        """When the transition from reasoning to content is clean (no mixed
        delta), no extra reasoning delta event should be emitted."""

        monkeypatch.setattr(envs, "VLLM_USE_EXPERIMENTAL_PARSER_CONTEXT", False)
        serving = _make_serving_instance_with_reasoning()

        delta_sequence = [
            DeltaMessage(reasoning="thinking"),
            DeltaMessage(content="answer"),
        ]
        _mock_parser_with_reasoning(serving, delta_sequence)

        contexts = [
            _make_simple_context_with_output("chunk1", [10]),
            _make_simple_context_with_output("chunk2", [20]),
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

        # Exactly one reasoning delta
        reasoning_deltas = [
            e for e in events if isinstance(e, ResponseReasoningTextDeltaEvent)
        ]
        assert len(reasoning_deltas) == 1
        assert reasoning_deltas[0].delta == "thinking"

        # Done event has just "thinking"
        reasoning_done = [
            e for e in events if isinstance(e, ResponseReasoningTextDoneEvent)
        ]
        assert len(reasoning_done) == 1
        assert reasoning_done[0].text == "thinking"

        # One content delta
        text_deltas = [e for e in events if isinstance(e, ResponseTextDeltaEvent)]
        assert len(text_deltas) == 1
        assert text_deltas[0].delta == "answer"