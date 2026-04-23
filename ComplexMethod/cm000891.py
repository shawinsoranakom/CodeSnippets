def test_strip_progress_preserves_compact_summaries(self):
        """strip_progress_entries doesn't strip isCompactSummary entries
        even though their type is 'summary' (in STRIPPABLE_TYPES)."""
        compact_summary = {
            "type": "summary",
            "uuid": "cs1",
            "isCompactSummary": True,
            "message": {"role": "user", "content": "compacted"},
        }
        regular_summary = {"type": "summary", "uuid": "s1", "message": {"content": "x"}}
        progress = {"type": "progress", "uuid": "p1", "data": {"stdout": "..."}}
        user = {
            "type": "user",
            "uuid": "u1",
            "message": {"role": "user", "content": "hi"},
        }

        content = _make_jsonl(compact_summary, regular_summary, progress, user)
        stripped = strip_progress_entries(content)
        stripped_entries = [
            json.loads(line) for line in stripped.strip().split("\n") if line.strip()
        ]

        uuids = [e.get("uuid") for e in stripped_entries]
        # compact_summary kept, regular_summary stripped, progress stripped, user kept
        assert "cs1" in uuids  # compact summary preserved
        assert "s1" not in uuids  # regular summary stripped
        assert "p1" not in uuids  # progress stripped
        assert "u1" in uuids