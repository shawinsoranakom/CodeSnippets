def test_iterable_non_canonical(self):
        # Canonical form is list of 2-tuple, but nested lists should work.
        choices = [
            ["C", _("Club")],
            ["D", _("Diamond")],
            ["H", _("Heart")],
            ["S", _("Spade")],
        ]
        self.assertEqual(normalize_choices(choices), self.expected)