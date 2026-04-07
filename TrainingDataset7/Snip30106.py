def test_unaccent_accentuated_needle(self):
        self.assertQuerySetEqual(
            self.Model.objects.filter(field__unaccent="aéÖ"),
            ["àéÖ", "aeO"],
            transform=lambda instance: instance.field,
            ordered=False,
        )