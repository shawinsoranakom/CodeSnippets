async def test_full_lifecycle_happy_path(self):
        """Fresh restore, append a turn, upload covers the session."""
        builder = TranscriptBuilder()
        prior = _make_transcript_content("user", "assistant")
        restore = TranscriptDownload(
            content=prior.encode("utf-8"), message_count=2, mode="sdk"
        )

        upload_mock = AsyncMock(return_value=None)
        with (
            patch(
                "backend.copilot.baseline.service.download_transcript",
                new=AsyncMock(return_value=restore),
            ),
            patch(
                "backend.copilot.baseline.service.upload_transcript",
                new=upload_mock,
            ),
        ):
            # --- 1. Restore & load prior session ---
            covers, _ = await _load_prior_transcript(
                user_id="user-1",
                session_id="session-1",
                session_messages=_make_session_messages("user", "assistant", "user"),
                transcript_builder=builder,
            )
            assert covers is True

            # --- 2. Append a new user turn + a new assistant response ---
            builder.append_user(content="follow-up question")
            _record_turn_to_transcript(
                LLMLoopResponse(
                    response_text="follow-up answer",
                    tool_calls=[],
                    raw_response=None,
                ),
                tool_results=None,
                transcript_builder=builder,
                model="test-model",
            )

            # --- 3. Gate + upload ---
            assert (
                should_upload_transcript(user_id="user-1", upload_safe=covers) is True
            )
            await _upload_final_transcript(
                user_id="user-1",
                session_id="session-1",
                transcript_builder=builder,
                session_msg_count=4,
            )

        upload_mock.assert_awaited_once()
        assert upload_mock.await_args is not None
        uploaded = upload_mock.await_args.kwargs["content"]
        assert b"follow-up question" in uploaded
        assert b"follow-up answer" in uploaded
        # Original prior-turn content preserved.
        assert b"user message 0" in uploaded
        assert b"assistant message 1" in uploaded