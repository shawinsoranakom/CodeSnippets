def test_nested_iterator_non_canonical(self):
        # Canonical form is list of 2-tuple, but nested lists should work.
        def generator():
            yield ["Audio", [["vinyl", _("Vinyl")], ["cd", _("CD")]]]
            yield ["Video", [["vhs", _("VHS Tape")], ["dvd", _("DVD")]]]
            yield ["unknown", _("Unknown")]

        choices = generator()
        self.assertEqual(normalize_choices(choices), self.expected_nested)