def test_full_compaction_lifecycle(self, tmp_path, monkeypatch):
        """Simulate the complete service.py compaction flow.

        Timeline:
        1. Previous turn uploaded transcript with [USER_1, ASST_1, USER_2, ASST_2]
        2. Current turn: download → load_previous
        3. User sends "Now show file2.py" → append_user
        4. SDK starts streaming response
        5. Mid-stream: PreCompact hook fires (context too large)
        6. CLI writes compaction summary to session file
        7. Next SDK message → emit_start (spinner)
        8. Following message → emit_end (CompactionResult)
        9. read_compacted_entries reads the session file
        10. replace_entries syncs TranscriptBuilder
        11. More assistant messages appended
        12. Export → upload → next turn downloads it
        """
        # --- Setup CLI projects directory ---
        config_dir = tmp_path / "config"
        projects_dir = config_dir / "projects"
        session_dir = projects_dir / "proj"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

        # --- Step 1-2: Load "downloaded" transcript from previous turn ---
        previous_transcript = _make_jsonl(
            USER_1,
            ASST_1_THINKING,
            ASST_1_TOOL,
            TOOL_RESULT_1,
            ASST_1_TEXT,
            USER_2,
            ASST_2,
        )
        builder = TranscriptBuilder()
        builder.load_previous(previous_transcript)
        assert builder.entry_count == 7

        # --- Step 3: User sends new query ---
        builder.append_user("Now show file2.py")
        assert builder.entry_count == 8

        # --- Step 4: SDK starts streaming ---
        builder.append_assistant(
            [{"type": "thinking", "thinking": "Let me read file2.py..."}],
            model="claude-sonnet-4-20250514",
        )
        assert builder.entry_count == 9

        # --- Step 5-6: PreCompact fires, CLI writes session file ---
        session_file = self._write_session_file(
            session_dir,
            [
                USER_1,
                ASST_1_THINKING,
                ASST_1_TOOL,
                PROGRESS_1,
                TOOL_RESULT_1,
                ASST_1_TEXT,
                USER_2,
                ASST_2,
                COMPACT_SUMMARY,
                POST_COMPACT_ASST,
                USER_3,
                ASST_3,
            ],
        )

        # --- Step 7: CompactionTracker receives PreCompact hook ---
        tracker = CompactionTracker()
        session = ChatSession.new(user_id="test-user", dry_run=False)
        tracker.on_compact(str(session_file))

        # --- Step 8: Next SDK message arrives → emit_start ---
        start_events = tracker.emit_start_if_ready()
        assert len(start_events) == 3
        assert isinstance(start_events[0], StreamStartStep)
        assert isinstance(start_events[1], StreamToolInputStart)
        assert isinstance(start_events[2], StreamToolInputAvailable)

        # Verify tool_call_id is set
        tool_call_id = start_events[1].toolCallId
        assert tool_call_id.startswith("compaction-")

        # --- Step 9: Following message → emit_end ---
        result = _run(tracker.emit_end_if_ready(session))
        assert result.just_ended is True
        assert result.transcript_path == str(session_file)
        assert len(result.events) == 2
        assert isinstance(result.events[0], StreamToolOutputAvailable)
        assert isinstance(result.events[1], StreamFinishStep)
        # Verify same tool_call_id
        assert result.events[0].toolCallId == tool_call_id

        # Session should have compaction messages persisted
        assert len(session.messages) == 2
        assert session.messages[0].role == "assistant"
        assert session.messages[1].role == "tool"

        # --- Step 10: read_compacted_entries + replace_entries ---
        compacted = read_compacted_entries(str(session_file))
        assert compacted is not None
        # Should have: COMPACT_SUMMARY + POST_COMPACT_ASST + USER_3 + ASST_3
        assert len(compacted) == 4
        assert compacted[0]["uuid"] == "cs1"
        assert compacted[0]["isCompactSummary"] is True

        # Replace builder state with compacted entries
        old_count = builder.entry_count
        builder.replace_entries(compacted)
        assert builder.entry_count == 4  # Only compacted entries
        assert builder.entry_count < old_count  # Compaction reduced entries

        # --- Step 11: More assistant messages after compaction ---
        builder.append_assistant(
            [{"type": "text", "text": "Here is file2.py:\n\ndef hello():\n    pass"}],
            model="claude-sonnet-4-20250514",
            stop_reason="end_turn",
        )
        assert builder.entry_count == 5

        # --- Step 12: Export for upload ---
        output = builder.to_jsonl()
        assert output  # Not empty
        output_entries = [json.loads(line) for line in output.strip().split("\n")]
        assert len(output_entries) == 5

        # Verify structure:
        # [COMPACT_SUMMARY, POST_COMPACT_ASST, USER_3, ASST_3, new_assistant]
        assert output_entries[0]["type"] == "summary"
        assert output_entries[0].get("isCompactSummary") is True
        assert output_entries[0]["uuid"] == "cs1"
        assert output_entries[1]["uuid"] == "a3"
        assert output_entries[2]["uuid"] == "u3"
        assert output_entries[3]["uuid"] == "a4"
        assert output_entries[4]["type"] == "assistant"

        # Verify parent chain is intact
        assert output_entries[1]["parentUuid"] == "cs1"  # a3 → cs1
        assert output_entries[2]["parentUuid"] == "a3"  # u3 → a3
        assert output_entries[3]["parentUuid"] == "u3"  # a4 → u3
        assert output_entries[4]["parentUuid"] == "a4"  # new → a4

        # --- Step 13: Roundtrip — next turn loads this export ---
        builder2 = TranscriptBuilder()
        builder2.load_previous(output)
        assert builder2.entry_count == 5

        # isCompactSummary survives roundtrip
        output2 = builder2.to_jsonl()
        first_entry = json.loads(output2.strip().split("\n")[0])
        assert first_entry.get("isCompactSummary") is True

        # Can append more messages
        builder2.append_user("What about file3.py?")
        assert builder2.entry_count == 6
        final_output = builder2.to_jsonl()
        last_entry = json.loads(final_output.strip().split("\n")[-1])
        assert last_entry["type"] == "user"
        # Parented to the last entry from previous turn
        assert last_entry["parentUuid"] == output_entries[-1]["uuid"]