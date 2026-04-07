def test_nested_choices(self):
        choices = [
            ("Audio", [("vinyl", _("Vinyl")), ("cd", _("CD"))]),
            ("Video", [("vhs", _("VHS Tape")), ("dvd", _("DVD"))]),
            ("unknown", _("Unknown")),
        ]
        expected = [
            ("vinyl", _("Vinyl")),
            ("cd", _("CD")),
            ("vhs", _("VHS Tape")),
            ("dvd", _("DVD")),
            ("unknown", _("Unknown")),
        ]
        result = flatten_choices(choices)
        self.assertIsInstance(result, collections.abc.Generator)
        self.assertEqual(list(result), expected)