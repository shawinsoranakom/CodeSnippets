def test_iterable(self):
        choices = [
            ("C", _("Club")),
            ("D", _("Diamond")),
            ("H", _("Heart")),
            ("S", _("Spade")),
        ]
        self.assertEqual(normalize_choices(choices), self.expected)