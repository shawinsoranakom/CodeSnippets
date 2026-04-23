def test_unaccent(self):
        self.assertQuerySetEqual(
            self.Model.objects.filter(field__unaccent="aeO"),
            ["àéÖ", "aeO"],
            transform=lambda instance: instance.field,
            ordered=False,
        )