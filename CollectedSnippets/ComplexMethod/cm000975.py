async def test_full_round_trip(self):
        prior = _make_transcript_content("user", "assistant")
        restore = TranscriptDownload(
            content=prior.encode("utf-8"), message_count=2, mode="sdk"
        )

        builder = TranscriptBuilder()
        with patch(
            "backend.copilot.baseline.service.download_transcript",
            new=AsyncMock(return_value=restore),
        ):
            covers, _ = await _load_prior_transcript(
                user_id="user-1",
                session_id="session-1",
                session_messages=_make_session_messages("user", "assistant", "user"),
                transcript_builder=builder,
            )
        assert covers is True
        assert builder.entry_count == 2

        # New user turn.
        builder.append_user(content="new question")
        assert builder.entry_count == 3

        # New assistant turn.
        response = LLMLoopResponse(
            response_text="new answer",
            tool_calls=[],
            raw_response=None,
        )
        _record_turn_to_transcript(
            response,
            tool_results=None,
            transcript_builder=builder,
            model="test-model",
        )
        assert builder.entry_count == 4

        # Upload.
        upload_mock = AsyncMock(return_value=None)
        with patch(
            "backend.copilot.baseline.service.upload_transcript",
            new=upload_mock,
        ):
            await _upload_final_transcript(
                user_id="user-1",
                session_id="session-1",
                transcript_builder=builder,
                session_msg_count=4,
            )

        upload_mock.assert_awaited_once()
        assert upload_mock.await_args is not None
        uploaded = upload_mock.await_args.kwargs["content"]
        assert b"new question" in uploaded
        assert b"new answer" in uploaded
        # Original content preserved in the round trip.
        assert b"user message 0" in uploaded
        assert b"assistant message 1" in uploaded