def test_trigram_search(self):
        self.assertQuerySetEqual(
            self.Model.objects.filter(field__trigram_similar="Mathew"),
            ["Matthew"],
            transform=lambda instance: instance.field,
        )