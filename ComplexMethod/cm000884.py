async def test_scenario_p_full_session_injected_on_mode_switch_t1(
        self, monkeypatch
    ):
        """Scenario P: fast→SDK T1 injects all baseline turns into the query."""
        # Simulate 4 baseline messages (2 turns) followed by the first SDK turn.
        session = _make_session(
            _msgs(
                ("user", "baseline-q1"),
                ("assistant", "baseline-a1"),
                ("user", "baseline-q2"),
                ("assistant", "baseline-a2"),
                ("user", "sdk-q1"),  # current SDK turn
            )
        )

        async def _mock_compress(msgs, target_tokens=None):
            return msgs, False

        monkeypatch.setattr(
            "backend.copilot.sdk.service._compress_messages", _mock_compress
        )

        # transcript_msg_count=4: baseline uploaded a transcript covering all
        # 4 prior messages, but use_resume=False (no CLI session from baseline).
        result, compacted = await _build_query_message(
            "sdk-q1",
            session,
            use_resume=False,
            transcript_msg_count=4,
            session_id="s",
        )

        # All baseline turns must appear — none of them can be silently dropped.
        assert "<conversation_history>" in result
        assert "baseline-q1" in result
        assert "baseline-a1" in result
        assert "baseline-q2" in result
        assert "baseline-a2" in result
        assert "Now, the user says:\nsdk-q1" in result
        assert compacted is False