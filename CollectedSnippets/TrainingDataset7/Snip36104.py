def test_nested_iterable(self):
        choices = [
            ("Audio", [("vinyl", _("Vinyl")), ("cd", _("CD"))]),
            ("Video", [("vhs", _("VHS Tape")), ("dvd", _("DVD"))]),
            ("unknown", _("Unknown")),
        ]
        self.assertEqual(normalize_choices(choices), self.expected_nested)