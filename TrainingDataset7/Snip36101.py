def test_iterator(self):
        def generator():
            yield "C", _("Club")
            yield "D", _("Diamond")
            yield "H", _("Heart")
            yield "S", _("Spade")

        choices = generator()
        self.assertEqual(normalize_choices(choices), self.expected)