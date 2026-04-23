def test_region_hierarchy_tracking(self):
        """Test that region is tracked for countries under region headers."""
        result = parse_template_1(self.VALID_LINES)

        # Find United States record
        us_records = [r for r in result["data"] if r["country"] == "United States"]
        assert len(us_records) > 0
        assert us_records[0]["region"] == "North America"

        # World Total should have region='World' and country='--'
        world_records = [
            r for r in result["data"] if r["region"] == "World" and r["country"] == "--"
        ]
        assert len(world_records) > 0