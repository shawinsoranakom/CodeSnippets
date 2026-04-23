def test_instance_unit_resolution(self, apple_10k_parsed):
        """Units should resolve to readable strings, not raw IDs."""
        _, units, facts = apple_10k_parsed

        unit_values = set(units.values())
        assert "iso4217:USD" in unit_values
        assert "shares" in unit_values

        compound = [v for v in unit_values if "/" in v]
        assert len(compound) > 0, "No compound units found (e.g. USD/share)"

        for tag, tag_facts in facts.items():
            for f in tag_facts:
                unit = f.get("unit")
                if unit:
                    assert (
                        "iso4217:" in unit
                        or unit in ("shares", "pure")
                        or "/" in unit
                        or ":" in unit
                    ), f"Unexpected unit format for {tag}: {unit}"