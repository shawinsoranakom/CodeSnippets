def test_parse_apple_10k_instance(self, apple_10k_parsed):
        """Parse Apple's 10-K XBRL instance with full resolution."""
        contexts, units, facts = apple_10k_parsed

        # Contexts
        assert len(contexts) > 10
        period_types = {ctx["period_type"] for ctx in contexts.values()}
        assert "instant" in period_types
        assert "duration" in period_types
        for ctx_id, ctx in contexts.items():
            assert ctx.get("entity"), f"Context {ctx_id} missing entity"

        # Units
        assert len(units) >= 2
        assert any("USD" in v for v in units.values())
        assert any("shares" in v.lower() for v in units.values())

        # Facts
        total_tags = len(facts)
        total_facts = sum(len(v) for v in facts.values())
        assert total_tags > 100, f"Only {total_tags} unique tags"
        assert total_facts > 500, f"Only {total_facts} total facts"

        wrong_prefix = [
            k for k in facts if k.startswith("20240928_") or k.startswith("2024_")
        ]
        assert wrong_prefix == [], f"Wrong-prefix tags: {wrong_prefix}"

        aapl_tags = [k for k in facts if k.startswith("aapl_")]
        ecd_tags = [k for k in facts if k.startswith("ecd_")]
        assert len(aapl_tags) > 0, "No aapl_ company extension tags found"
        assert len(ecd_tags) > 0, "No ecd_ tags found"