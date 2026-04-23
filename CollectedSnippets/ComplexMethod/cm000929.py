def test_backoff_capped_at_30s(self):
        """_compute_transient_backoff must be capped at _MAX_TRANSIENT_BACKOFF_SECONDS.

        With max_transient_retries=10, uncapped 2^9=512s would stall users
        for 8+ minutes.  _compute_transient_backoff caps at 30s.

        Full-jitter (0.5 … 1.0 × base) is applied for thundering-herd
        prevention, so each call returns a value in [base//2, base] rather
        than an exact integer.  We verify bounds instead of exact values.
        """
        from backend.copilot.sdk.service import (
            _MAX_TRANSIENT_BACKOFF_SECONDS,
            _compute_transient_backoff,
        )

        # attempt=1: base=1, jitter range [1, 1] (max(1, round(1 * [0.5,1.0])))
        v1 = _compute_transient_backoff(1)
        assert v1 >= 1

        # attempt=2: base=2, jitter range [1, 2]
        v2 = _compute_transient_backoff(2)
        assert 1 <= v2 <= 2

        # attempt=3: base=4, jitter range [2, 4]
        v3 = _compute_transient_backoff(3)
        assert 2 <= v3 <= 4

        # attempt=4: base=8, jitter range [4, 8]
        v4 = _compute_transient_backoff(4)
        assert 4 <= v4 <= 8

        # attempt=5: base=16, jitter range [8, 16]
        v5 = _compute_transient_backoff(5)
        assert 8 <= v5 <= 16

        # attempt=6: base capped at 30, jitter range [15, 30]
        v6 = _compute_transient_backoff(6)
        assert 15 <= v6 <= _MAX_TRANSIENT_BACKOFF_SECONDS

        # attempt=10: still capped
        v10 = _compute_transient_backoff(10)
        assert v10 <= _MAX_TRANSIENT_BACKOFF_SECONDS