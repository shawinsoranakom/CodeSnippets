def test_full_compaction_roundtrip(self, tmp_path, monkeypatch):
        """Full roundtrip: load → append → compact → replace → export."""
        # Setup: create a CLI session file with pre-compact + compaction entries
        config_dir = tmp_path / "config"
        projects_dir = config_dir / "projects"
        session_dir = projects_dir / "proj"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

        # Simulate a transcript with old messages, then a compaction summary
        old_user = {
            "type": "user",
            "uuid": "u1",
            "message": {"role": "user", "content": "old question"},
        }
        old_asst = {
            "type": "assistant",
            "uuid": "a1",
            "parentUuid": "u1",
            "message": {"role": "assistant", "content": "old answer"},
        }
        compact_summary = {
            "type": "summary",
            "uuid": "cs1",
            "isCompactSummary": True,
            "message": {"role": "user", "content": "compacted summary of conversation"},
        }
        post_compact_asst = {
            "type": "assistant",
            "uuid": "a2",
            "parentUuid": "cs1",
            "message": {"role": "assistant", "content": "response after compaction"},
        }
        session_file = session_dir / "session.jsonl"
        session_file.write_text(
            _make_jsonl(old_user, old_asst, compact_summary, post_compact_asst)
        )

        # Step 1: TranscriptBuilder loads previous transcript (simulates download)
        # The previous transcript would have the OLD entries (pre-compaction)
        previous_transcript = _make_jsonl(old_user, old_asst)
        builder = TranscriptBuilder()
        builder.load_previous(previous_transcript)
        assert builder.entry_count == 2

        # Step 2: New messages appended during the current query
        builder.append_user("new question")
        builder.append_assistant([{"type": "text", "text": "new answer"}])
        assert builder.entry_count == 4

        # Step 3: read_compacted_entries reads the CLI session file
        compacted = read_compacted_entries(str(session_file))
        assert compacted is not None
        assert len(compacted) == 2  # compact_summary + post_compact_asst
        assert compacted[0]["isCompactSummary"] is True

        # Step 4: replace_entries syncs builder with CLI state
        builder.replace_entries(compacted)
        assert builder.entry_count == 2  # Only compacted entries now

        # Step 5: Append post-compaction messages (continuing the stream)
        builder.append_user("follow-up question")
        assert builder.entry_count == 3

        # Step 6: Export and verify
        output = builder.to_jsonl()
        entries = [json.loads(line) for line in output.strip().split("\n")]
        assert len(entries) == 3
        # First entry is the compaction summary
        assert entries[0]["type"] == "summary"
        assert entries[0]["uuid"] == "cs1"
        # Second is the post-compact assistant
        assert entries[1]["uuid"] == "a2"
        # Third is our follow-up, parented to the last compacted entry
        assert entries[2]["type"] == "user"
        assert entries[2]["parentUuid"] == "a2"