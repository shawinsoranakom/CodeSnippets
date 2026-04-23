def test_small_chunks_after_first_buffer_until_threshold(self):
        # Generous time threshold so size alone controls flush timing.
        emitter = BaselineReasoningEmitter(
            coalesce_min_chars=32, coalesce_max_interval_ms=60_000
        )
        # First chunk always flushes immediately (so UI renders without
        # waiting).
        first = emitter.on_delta(_delta(reasoning="hi "))
        assert any(isinstance(e, StreamReasoningStart) for e in first)
        assert sum(isinstance(e, StreamReasoningDelta) for e in first) == 1

        # Subsequent small chunks buffer silently — 5 × 4 chars = 20 chars,
        # still under the 32-char threshold.
        for _ in range(5):
            assert emitter.on_delta(_delta(reasoning="abcd")) == []

        # Once the threshold is crossed, the accumulated buffer flushes
        # as a single StreamReasoningDelta carrying every buffered chunk.
        flush = emitter.on_delta(_delta(reasoning="efghijklmnop"))
        assert len(flush) == 1
        assert isinstance(flush[0], StreamReasoningDelta)
        assert flush[0].delta == "abcd" * 5 + "efghijklmnop"