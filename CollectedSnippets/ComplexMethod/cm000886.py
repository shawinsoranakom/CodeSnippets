def test_persists_to_session(self):
        session = _make_session()
        assert len(session.messages) == 0
        evts = emit_compaction(session)
        assert len(evts) == 5
        # Should have appended 2 messages (assistant tool call + tool result)
        assert len(session.messages) == 2
        assert session.messages[0].role == "assistant"
        assert session.messages[0].tool_calls is not None
        assert (
            session.messages[0].tool_calls[0]["function"]["name"]
            == COMPACTION_TOOL_NAME
        )
        assert session.messages[1].role == "tool"
        assert session.messages[1].content == COMPACTION_DONE_MSG