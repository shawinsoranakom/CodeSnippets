async def test_baseline_mode_context_messages_from_transcript_content(
        self, tmp_path
    ):
        """mode='baseline' → context_messages populated from transcript content + gap.

        When a baseline-mode transcript exists, extract_context_messages converts
        the JSONL content to ChatMessage objects and returns them in context_messages.
        use_resume must remain False.
        """
        import json as stdlib_json
        from datetime import UTC, datetime

        from backend.copilot.model import ChatMessage, ChatSession
        from backend.copilot.transcript import STOP_REASON_END_TURN, TranscriptDownload
        from backend.copilot.transcript_builder import TranscriptBuilder

        # Build a minimal valid JSONL transcript with 2 messages
        lines = [
            stdlib_json.dumps(
                {
                    "type": "user",
                    "uuid": "uid-0",
                    "parentUuid": "",
                    "message": {"role": "user", "content": "TRANSCRIPT_USER"},
                }
            ),
            stdlib_json.dumps(
                {
                    "type": "assistant",
                    "uuid": "uid-1",
                    "parentUuid": "uid-0",
                    "message": {
                        "role": "assistant",
                        "id": "msg_1",
                        "model": "test",
                        "type": "message",
                        "stop_reason": STOP_REASON_END_TURN,
                        "content": [{"type": "text", "text": "TRANSCRIPT_ASSISTANT"}],
                    },
                }
            ),
        ]
        content = ("\n".join(lines) + "\n").encode("utf-8")

        session = ChatSession(
            session_id="test-session",
            user_id="user-1",
            messages=[
                ChatMessage(role="user", content="DB_USER"),
                ChatMessage(role="assistant", content="DB_ASSISTANT"),
                ChatMessage(role="user", content="current turn"),
            ],
            title="test",
            usage=[],
            started_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        builder = TranscriptBuilder()
        baseline_restore = TranscriptDownload(
            content=content,
            message_count=2,
            mode="baseline",
        )

        import backend.copilot.sdk.service as _svc_mod

        with (
            patch(
                "backend.copilot.sdk.service.download_transcript",
                new=AsyncMock(return_value=baseline_restore),
            ),
            patch.object(_svc_mod.config, "claude_agent_use_resume", True),
        ):
            result = await _restore_cli_session_for_turn(
                user_id="user-1",
                session_id="test-session",
                session=session,
                sdk_cwd=str(tmp_path),
                transcript_builder=builder,
                log_prefix="[Test]",
            )

        assert result.use_resume is False
        assert result.context_messages is not None
        # Transcript content has 2 messages, no gap (watermark=2, session prior=2)
        assert len(result.context_messages) == 2
        assert result.context_messages[0].role == "user"
        assert result.context_messages[1].role == "assistant"
        assert "TRANSCRIPT_ASSISTANT" in (result.context_messages[1].content or "")
        # transcript_content must be non-empty so the _seed_transcript guard in
        # stream_chat_completion_sdk skips DB reconstruction (which would duplicate
        # builder entries since load_previous appends).
        assert result.transcript_content != ""