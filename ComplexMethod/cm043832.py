def test_parse_calculation_us_gaap(self, us_gaap_cal_bytes):
        """Should parse calculation relationships."""
        p = XBRLParser()
        calculations = p.parse_calculation(
            BytesIO(us_gaap_cal_bytes), TaxonomyStyle.FASB_STANDARD
        )

        assert isinstance(calculations, dict)
        assert len(calculations) > 0

        for child_id, info in calculations.items():
            assert isinstance(child_id, str)
            assert isinstance(info, dict)
            assert "order" in info
            assert "weight" in info
            assert "parent_tag" in info
            assert isinstance(info["weight"], (int, float))
            assert isinstance(info["parent_tag"], str)