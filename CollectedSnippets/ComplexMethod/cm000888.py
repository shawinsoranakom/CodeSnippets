async def test_multiple_pending_hooks_are_counted_even_before_completion(self):
        tracker = CompactionTracker()
        session = _make_session()

        tracker.on_compact("/path/1")
        tracker.emit_start_if_ready()
        tracker.on_compact("/path/2")
        tracker.on_compact("/path/3")

        result1 = await tracker.emit_end_if_ready(session)
        assert result1.just_ended is True
        assert result1.transcript_path == "/path/1"
        assert tracker.attempt_count == 3
        assert tracker.completed_count == 1

        tracker.emit_start_if_ready()
        result2 = await tracker.emit_end_if_ready(session)
        assert result2.just_ended is True
        assert result2.transcript_path == "/path/2"

        tracker.emit_start_if_ready()
        result3 = await tracker.emit_end_if_ready(session)
        assert result3.just_ended is True
        assert result3.transcript_path == "/path/3"
        assert tracker.completed_count == 3