def test_nested_mixed_mapping_and_iterable(self):
        # Although not documented, as it's better to stick to either mappings
        # or iterables, nesting of mappings within iterables and vice versa
        # works and is likely to occur in the wild. This is supported by the
        # recursive call to `normalize_choices()` which will normalize nested
        # choices.
        choices = {
            "Audio": [("vinyl", _("Vinyl")), ("cd", _("CD"))],
            "Video": [("vhs", _("VHS Tape")), ("dvd", _("DVD"))],
            "unknown": _("Unknown"),
        }
        self.assertEqual(normalize_choices(choices), self.expected_nested)
        choices = [
            ("Audio", {"vinyl": _("Vinyl"), "cd": _("CD")}),
            ("Video", {"vhs": _("VHS Tape"), "dvd": _("DVD")}),
            ("unknown", _("Unknown")),
        ]
        self.assertEqual(normalize_choices(choices), self.expected_nested)