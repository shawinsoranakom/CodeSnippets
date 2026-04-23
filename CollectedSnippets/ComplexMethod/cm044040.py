def test_extracts_units_from_header(self):
        """Test that units are extracted from header line."""
        result = parse_template_1(self.VALID_LINES)

        # Find Area record and check unit
        area_records = [r for r in result["data"] if r["attribute"] == "Area"]
        assert len(area_records) > 0
        assert area_records[0]["unit"] == "Mil hectares"

        # Find Yield record and check unit
        yield_records = [r for r in result["data"] if r["attribute"] == "Yield"]
        assert len(yield_records) > 0
        assert yield_records[0]["unit"] == "MT/HA"

        # Find Production record (base or change) and check unit
        prod_records = [
            r
            for r in result["data"]
            if "Production" in r["attribute"] and "%" not in r["attribute"]
        ]
        assert len(prod_records) > 0
        assert prod_records[0]["unit"] == "MMT"