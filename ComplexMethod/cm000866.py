def test_basic_fields(self):
        entry = CoPilotExecutionEntry(
            session_id="s1",
            user_id="u1",
            message="hello",
        )
        assert entry.session_id == "s1"
        assert entry.user_id == "u1"
        assert entry.message == "hello"
        assert entry.is_user_message is True
        assert entry.mode is None
        assert entry.context is None
        assert entry.file_ids is None