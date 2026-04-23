def test_groups_property(self):
        """Country should expose membership groups."""
        c = Country("US")
        groups = c.groups
        assert isinstance(groups, list)
        assert "G7" in groups
        assert "G20" in groups
        assert "NATO" in groups
        assert "OECD" in groups
        # US is not a member of these
        assert "EU" not in groups
        assert "OPEC" not in groups