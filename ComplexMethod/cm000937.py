async def test_baseline_mode_gap_present_context_includes_gap(self, tmp_path):
        """mode='baseline' + gap → context_messages includes transcript msgs and gap."""
        import json as stdlib_json
        from datetime import UTC, datetime

        from backend.copilot.model import ChatMessage, ChatSession
        from backend.copilot.transcript import STOP_REASON_END_TURN, TranscriptDownload
        from backend.copilot.transcript_builder import TranscriptBuilder

        # Transcript covers only 2 messages; session has 4 prior + current turn
        lines = [
            stdlib_json.dumps(
                {
                    "type": "user",
                    "uuid": "uid-0",
                    "parentUuid": "",
                    "message": {"role": "user", "content": "TRANSCRIPT_USER_0"},
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
                        "content": [{"type": "text", "text": "TRANSCRIPT_ASSISTANT_1"}],
                    },
                }
            ),
        ]
        content = ("\n".join(lines) + "\n").encode("utf-8")

        session = ChatSession(
            session_id="test-session",
            user_id="user-1",
            messages=[
                ChatMessage(role="user", content="DB_USER_0"),
                ChatMessage(role="assistant", content="DB_ASSISTANT_1"),
                ChatMessage(role="user", content="GAP_USER_2"),
                ChatMessage(role="assistant", content="GAP_ASSISTANT_3"),
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
            message_count=2,  # watermark=2; session has 4 prior → gap of 2
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
        # 2 from transcript + 2 gap messages = 4 total
        assert len(result.context_messages) == 4
        roles = [m.role for m in result.context_messages]
        assert roles == ["user", "assistant", "user", "assistant"]
        # Gap messages come from DB (ChatMessage objects)
        gap_user = result.context_messages[2]
        gap_asst = result.context_messages[3]
        assert gap_user.content == "GAP_USER_2"
        assert gap_asst.content == "GAP_ASSISTANT_3"