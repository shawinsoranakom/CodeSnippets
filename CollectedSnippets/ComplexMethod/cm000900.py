def test_double_compaction_within_session(self, tmp_path, monkeypatch):
        """Two compactions in the same session (across reset_for_query)."""
        config_dir = tmp_path / "config"
        projects_dir = config_dir / "projects"
        session_dir = projects_dir / "proj"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

        tracker = CompactionTracker()
        session = ChatSession.new(user_id="test", dry_run=False)
        builder = TranscriptBuilder()

        # --- First query with compaction ---
        builder.append_user("first question")
        builder.append_assistant([{"type": "text", "text": "first answer"}])

        # Write session file for first compaction
        first_summary = {
            "type": "summary",
            "uuid": "cs-first",
            "isCompactSummary": True,
            "message": {"role": "user", "content": "First compaction summary"},
        }
        first_post = {
            "type": "assistant",
            "uuid": "a-first",
            "parentUuid": "cs-first",
            "message": {"role": "assistant", "content": "first post-compact"},
        }
        file1 = session_dir / "session1.jsonl"
        file1.write_text(_make_jsonl(first_summary, first_post))

        tracker.on_compact(str(file1))
        tracker.emit_start_if_ready()
        result1 = _run(tracker.emit_end_if_ready(session))
        assert result1.just_ended is True

        compacted1 = read_compacted_entries(str(file1))
        assert compacted1 is not None
        builder.replace_entries(compacted1)
        assert builder.entry_count == 2

        # --- Reset for second query ---
        tracker.reset_for_query()

        # --- Second query with compaction ---
        builder.append_user("second question")
        builder.append_assistant([{"type": "text", "text": "second answer"}])

        second_summary = {
            "type": "summary",
            "uuid": "cs-second",
            "isCompactSummary": True,
            "message": {"role": "user", "content": "Second compaction summary"},
        }
        second_post = {
            "type": "assistant",
            "uuid": "a-second",
            "parentUuid": "cs-second",
            "message": {"role": "assistant", "content": "second post-compact"},
        }
        file2 = session_dir / "session2.jsonl"
        file2.write_text(_make_jsonl(second_summary, second_post))

        tracker.on_compact(str(file2))
        tracker.emit_start_if_ready()
        result2 = _run(tracker.emit_end_if_ready(session))
        assert result2.just_ended is True

        compacted2 = read_compacted_entries(str(file2))
        assert compacted2 is not None
        builder.replace_entries(compacted2)
        assert builder.entry_count == 2  # Only second compaction entries

        # Export and verify
        output = builder.to_jsonl()
        entries = [json.loads(line) for line in output.strip().split("\n")]
        assert entries[0]["uuid"] == "cs-second"
        assert entries[0].get("isCompactSummary") is True