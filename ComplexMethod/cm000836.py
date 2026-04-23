def test_compact_summary_entries_preserved(self):
        """``isCompactSummary=True`` entries survive ``_transcript_to_messages``."""
        import json as stdlib_json

        from .transcript import STOP_REASON_END_TURN

        # Build a transcript where one entry is a compaction summary.
        # isCompactSummary=True entries have type in STRIPPABLE_TYPES but are kept.
        compact_entry = stdlib_json.dumps(
            {
                "type": "summary",
                "uuid": "uid-compact",
                "parentUuid": "",
                "isCompactSummary": True,
                "message": {
                    "role": "user",
                    "content": "COMPACT_SUMMARY_CONTENT",
                },
            }
        )
        assistant_entry = stdlib_json.dumps(
            {
                "type": "assistant",
                "uuid": "uid-1",
                "parentUuid": "uid-compact",
                "message": {
                    "role": "assistant",
                    "id": "msg_1",
                    "model": "test",
                    "type": "message",
                    "stop_reason": STOP_REASON_END_TURN,
                    "content": [{"type": "text", "text": "response after compact"}],
                },
            }
        )
        content = compact_entry + "\n" + assistant_entry + "\n"
        dl = TranscriptDownload(
            content=content.encode("utf-8"), message_count=2, mode="sdk"
        )
        messages = _msgs("user", "assistant", "user")
        result = extract_context_messages(dl, messages)
        # Both the compact summary and the assistant response are present
        assert len(result) == 2
        roles = [m.role for m in result]
        assert "user" in roles  # compact summary has role=user
        assert "assistant" in roles
        # The compact summary content is preserved
        compact_msgs = [m for m in result if m.role == "user"]
        assert any("COMPACT_SUMMARY_CONTENT" in (m.content or "") for m in compact_msgs)