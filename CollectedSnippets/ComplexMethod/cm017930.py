def test_partial_numbering_pattern_regex(self):
        """Test that the partial numbering regex pattern correctly matches."""

        # Should match partial numbering patterns
        assert PARTIAL_NUMBERING_PATTERN.match(".1") is not None
        assert PARTIAL_NUMBERING_PATTERN.match(".2") is not None
        assert PARTIAL_NUMBERING_PATTERN.match(".10") is not None
        assert PARTIAL_NUMBERING_PATTERN.match(".99") is not None

        # Should NOT match other patterns
        assert PARTIAL_NUMBERING_PATTERN.match("1.") is None
        assert PARTIAL_NUMBERING_PATTERN.match("1.2") is None
        assert PARTIAL_NUMBERING_PATTERN.match(".1.2") is None
        assert PARTIAL_NUMBERING_PATTERN.match("text") is None
        assert PARTIAL_NUMBERING_PATTERN.match(".a") is None
        assert PARTIAL_NUMBERING_PATTERN.match("") is None