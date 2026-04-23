async def test_multiple_compactions_within_query(self):
        """Two mid-stream compactions within a single query both trigger."""
        tracker = CompactionTracker()
        session = _make_session()

        # First compaction cycle
        tracker.on_compact("/path/1")
        tracker.emit_start_if_ready()
        result1 = await tracker.emit_end_if_ready(session)
        assert result1.just_ended is True
        assert len(result1.events) == 2
        assert result1.transcript_path == "/path/1"

        # Second compaction cycle in the same query
        tracker.on_compact("/path/2")
        start_evts = tracker.emit_start_if_ready()
        assert len(start_evts) == 3
        result2 = await tracker.emit_end_if_ready(session)
        assert result2.just_ended is True
        assert result2.transcript_path == "/path/2"
        assert tracker.completed_count == 2