def test_non_empty(self):
        choices = [
            ("C", _("Club")),
            ("D", _("Diamond")),
            ("H", _("Heart")),
            ("S", _("Spade")),
        ]
        result = flatten_choices(choices)
        self.assertIsInstance(result, collections.abc.Generator)
        self.assertEqual(list(result), choices)