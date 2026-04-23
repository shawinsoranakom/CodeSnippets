def test_defaults(self):
        state = _BaselineStreamState()
        # ``pending_events`` is an asyncio.Queue now (live SSE channel).
        # The durable inspection view is ``emitted_events``.
        assert state.pending_events.empty()
        assert state.emitted_events == []
        assert state.assistant_text == ""
        assert state.text_started is False
        assert state.turn_prompt_tokens == 0
        assert state.turn_completion_tokens == 0
        assert state.text_block_id