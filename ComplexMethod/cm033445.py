def test_result_default_values(self):
        """Test default values."""
        result = VerificationResult(
            es_index="test",
            ob_table="test",
        )

        assert result.count_match is False
        assert result.count_diff == 0
        assert result.sample_size == 0
        assert result.samples_verified == 0
        assert result.samples_matched == 0
        assert result.sample_match_rate == 0.0
        assert result.missing_in_ob == []
        assert result.data_mismatches == []
        assert result.message == ""