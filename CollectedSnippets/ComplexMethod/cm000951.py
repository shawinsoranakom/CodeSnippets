async def test_scenario_f_no_resume_always_injects_full_session(self, monkeypatch):
        """Scenario F: use_resume=False with transcript_msg_count > 0 still injects
        the FULL prior session — not just the gap since the transcript end.

        When there is no --resume the CLI starts with zero context, so injecting
        only the post-transcript gap would silently drop all transcript-covered
        history.  The correct fix is to always compress the full session.
        """
        session = _make_session(
            _msgs(
                ("user", "q1"),  # transcript_msg_count=2 covers these
                ("assistant", "a1"),
                ("user", "q2"),  # post-transcript gap starts here
                ("assistant", "a2"),
                ("user", "q3"),  # current message
            )
        )
        compressed_msgs: list[list] = []

        async def _mock_compress(msgs, target_tokens=None):
            compressed_msgs.append(list(msgs))
            return msgs, False

        monkeypatch.setattr(
            "backend.copilot.sdk.service._compress_messages", _mock_compress
        )

        result, _ = await _build_query_message(
            "q3",
            session,
            use_resume=False,
            transcript_msg_count=2,  # transcript covers q1/a1 but no --resume
            session_id="s",
        )
        assert "<conversation_history>" in result
        # Full session must be injected — transcript-covered turns ARE included
        assert "q1" in result
        assert "a1" in result
        assert "q2" in result
        assert "a2" in result
        assert "Now, the user says:\nq3" in result
        # Compressed exactly once with all 4 prior messages
        assert len(compressed_msgs) == 1
        assert len(compressed_msgs[0]) == 4