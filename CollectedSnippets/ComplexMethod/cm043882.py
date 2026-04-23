def test_detect_unit_dimension(self, mock_metadata_unit):
        """Test detection of UNIT dimension."""
        transform_dim, unit_dim, transform_lookup, unit_lookup = (
            detect_transform_dimension("MFS_MA")
        )

        assert transform_dim is None
        assert unit_dim == "UNIT"
        assert "usd" in unit_lookup
        assert "eur" in unit_lookup
        assert "local" in unit_lookup
        assert "index" in unit_lookup
        assert unit_lookup["usd"] == "USD"
        assert unit_lookup["eur"] == "EUR"
        assert unit_lookup["local"] == "XDC"