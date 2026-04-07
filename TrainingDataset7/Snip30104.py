def test_unaccent_chained(self):
        """
        Unaccent can be used chained with a lookup (which should be the case
        since unaccent implements the Transform API)
        """
        self.assertQuerySetEqual(
            self.Model.objects.filter(field__unaccent__iexact="aeO"),
            ["àéÖ", "aeO", "aeo"],
            transform=lambda instance: instance.field,
            ordered=False,
        )
        self.assertQuerySetEqual(
            self.Model.objects.filter(field__unaccent__endswith="éÖ"),
            ["àéÖ", "aeO"],
            transform=lambda instance: instance.field,
            ordered=False,
        )