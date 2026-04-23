def test_nested_iterable_non_canonical(self):
        # Canonical form is list of 2-tuple, but nested lists should work.
        choices = [
            ["Audio", [["vinyl", _("Vinyl")], ["cd", _("CD")]]],
            ["Video", [["vhs", _("VHS Tape")], ["dvd", _("DVD")]]],
            ["unknown", _("Unknown")],
        ]
        self.assertEqual(normalize_choices(choices), self.expected_nested)