def test_instance_presentation_metadata(self, apple_10k_parsed):
        """Facts should have presentation metadata (table, parent, order)."""
        _, _, facts = apple_10k_parsed

        with_pres = sum(
            1 for tag_facts in facts.values() if tag_facts[0].get("presentation")
        )
        assert with_pres > 0, "No facts have presentation metadata"

        for tag_facts in facts.values():
            pres = tag_facts[0].get("presentation")
            if pres:
                entry = pres[0]
                assert "table" in entry
                assert "parent" in entry
                assert "order" in entry
                break