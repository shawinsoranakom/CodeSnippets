async def test_reasoning_only_stream_no_content(self, monkeypatch):
        """When the stream has only reasoning deltas and no content, the
        reasoning done event should be emitted at finalization with the
        full accumulated text, and no text delta events should appear."""

        monkeypatch.setattr(envs, "VLLM_USE_EXPERIMENTAL_PARSER_CONTEXT", False)
        serving = _make_serving_instance_with_reasoning()

        delta_sequence = [
            DeltaMessage(reasoning="step 1"),
            DeltaMessage(reasoning=" step 2"),
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

        # Two reasoning deltas
        reasoning_deltas = [
            e for e in events if isinstance(e, ResponseReasoningTextDeltaEvent)
        ]
        assert len(reasoning_deltas) == 2
        assert reasoning_deltas[0].delta == "step 1"
        assert reasoning_deltas[1].delta == " step 2"

        # Done event at finalization with accumulated text
        reasoning_done = [
            e for e in events if isinstance(e, ResponseReasoningTextDoneEvent)
        ]
        assert len(reasoning_done) == 1
        assert reasoning_done[0].text == "step 1 step 2"

        # No content text deltas
        text_deltas = [e for e in events if isinstance(e, ResponseTextDeltaEvent)]
        assert len(text_deltas) == 0

        # Final item should be a reasoning item
        item_done_events = [
            e for e in events if isinstance(e, ResponseOutputItemDoneEvent)
        ]
        assert len(item_done_events) == 1
        assert isinstance(item_done_events[0].item, ResponseReasoningItem)