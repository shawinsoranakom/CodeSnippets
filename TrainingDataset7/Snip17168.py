def test_chaining_transforms(self):
        Company.objects.create(name=" Django Software Foundation  ")
        Company.objects.create(name="Yahoo")
        with register_lookup(CharField, Trim), register_lookup(CharField, Length):
            for expr in [Length("name__trim"), F("name__trim__length")]:
                with self.subTest(expr=expr):
                    self.assertCountEqual(
                        Company.objects.annotate(length=expr).values("name", "length"),
                        [
                            {"name": " Django Software Foundation  ", "length": 26},
                            {"name": "Yahoo", "length": 5},
                        ],
                    )