def test_detect_transform_dimension(self, mock_metadata_transform):
        """Test detection of TRANSFORM dimension."""
        transform_dim, unit_dim, transform_lookup, unit_lookup = (
            detect_transform_dimension("CPI")
        )

        assert transform_dim == "TRANSFORMATION"
        assert unit_dim is None
        assert "index" in transform_lookup
        assert "yoy" in transform_lookup
        assert "period" in transform_lookup
        assert transform_lookup["index"] == "IX"
        assert transform_lookup["yoy"] == "PC_PA"
        assert transform_lookup["period"] == "PC_PP"