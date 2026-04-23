async def test_reasoning_then_text_emits_paired_events(self):
        state = _BaselineStreamState(model="anthropic/claude-sonnet-4-6")

        chunks = [
            _make_delta_chunk(reasoning="thinking..."),
            _make_delta_chunk(reasoning=" more"),
            _make_delta_chunk(content="final answer"),
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_stream_mock(*chunks)
        )

        with patch(
            "backend.copilot.baseline.service._get_openai_client",
            return_value=mock_client,
        ):
            await _baseline_llm_caller(
                messages=[{"role": "user", "content": "hi"}],
                tools=[],
                state=state,
            )

        types = [type(e).__name__ for e in state.emitted_events]
        assert "StreamReasoningStart" in types
        assert "StreamReasoningDelta" in types
        assert "StreamReasoningEnd" in types

        # Reasoning must close before text opens — AI SDK v5 rejects
        # interleaved reasoning / text parts.
        reason_end = types.index("StreamReasoningEnd")
        text_start = types.index("StreamTextStart")
        assert reason_end < text_start

        # All reasoning deltas share a single block id; the text block uses
        # a fresh id after the reasoning-end rotation.
        reasoning_ids = {
            e.id
            for e in state.emitted_events
            if isinstance(
                e, (StreamReasoningStart, StreamReasoningDelta, StreamReasoningEnd)
            )
        }
        text_ids = {
            e.id
            for e in state.emitted_events
            if isinstance(e, (StreamTextStart, StreamTextDelta, StreamTextEnd))
        }
        assert len(reasoning_ids) == 1
        assert len(text_ids) == 1
        assert reasoning_ids.isdisjoint(text_ids)

        combined = "".join(
            e.delta for e in state.emitted_events if isinstance(e, StreamReasoningDelta)
        )
        assert combined == "thinking... more"