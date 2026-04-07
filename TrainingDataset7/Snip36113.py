def test_iterable_set(self):
        # Although not documented, as sets are unordered which results in
        # randomised order in form fields, passing a set of 2-tuples works.
        # Consistent ordering of choices on model fields in migrations is
        # enforced by the migrations serializer.
        choices = {
            ("C", _("Club")),
            ("D", _("Diamond")),
            ("H", _("Heart")),
            ("S", _("Spade")),
        }
        self.assertEqual(sorted(normalize_choices(choices)), sorted(self.expected))