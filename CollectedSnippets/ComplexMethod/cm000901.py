def test_strip_progress_then_load_then_compact_roundtrip(
        self, tmp_path, monkeypatch
    ):
        """Full pipeline: strip → load → compact → replace → export → reload.

        This tests the exact sequence that happens across two turns:
        Turn 1: SDK produces transcript with progress entries
        Upload: strip_progress_entries removes progress, upload to cloud
        Turn 2: Download → load_previous → compaction fires → replace → export
        Turn 3: Download the Turn 2 export → load_previous (roundtrip)
        """
        config_dir = tmp_path / "config"
        projects_dir = config_dir / "projects"
        session_dir = projects_dir / "proj"
        session_dir.mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

        # --- Turn 1: SDK produces raw transcript ---
        raw_content = _make_jsonl(
            USER_1,
            ASST_1_THINKING,
            ASST_1_TOOL,
            PROGRESS_1,
            TOOL_RESULT_1,
            ASST_1_TEXT,
            USER_2,
            ASST_2,
        )

        # Strip progress for upload
        stripped = strip_progress_entries(raw_content)
        stripped_entries = [
            json.loads(line) for line in stripped.strip().split("\n") if line.strip()
        ]
        # Progress should be gone
        assert not any(e.get("type") == "progress" for e in stripped_entries)
        assert len(stripped_entries) == 7  # 8 - 1 progress

        # --- Turn 2: Download stripped, load, compaction happens ---
        builder = TranscriptBuilder()
        builder.load_previous(stripped)
        assert builder.entry_count == 7

        builder.append_user("Now show file2.py")
        builder.append_assistant(
            [{"type": "text", "text": "Reading file2.py..."}],
            model="claude-sonnet-4-20250514",
        )

        # CLI writes session file with compaction
        session_file = self._write_session_file(
            session_dir,
            [
                USER_1,
                ASST_1_TOOL,
                TOOL_RESULT_1,
                ASST_1_TEXT,
                USER_2,
                ASST_2,
                COMPACT_SUMMARY,
                POST_COMPACT_ASST,
            ],
        )

        compacted = read_compacted_entries(str(session_file))
        assert compacted is not None
        builder.replace_entries(compacted)

        # Append post-compaction message
        builder.append_user("Thanks!")
        output = builder.to_jsonl()

        # --- Turn 3: Fresh load of Turn 2 export ---
        builder3 = TranscriptBuilder()
        builder3.load_previous(output)
        # Should have: compact_summary + post_compact_asst + "Thanks!"
        assert builder3.entry_count == 3

        # Compact summary survived the full pipeline
        first = json.loads(builder3.to_jsonl().strip().split("\n")[0])
        assert first.get("isCompactSummary") is True
        assert first["type"] == "summary"