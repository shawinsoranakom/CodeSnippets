def test_bilateral_multi_value(self):
        with register_lookup(models.CharField, UpperBilateralTransform):
            Author.objects.bulk_create(
                [
                    Author(name="Foo"),
                    Author(name="Bar"),
                    Author(name="Ray"),
                ]
            )
            self.assertQuerySetEqual(
                Author.objects.filter(name__upper__in=["foo", "bar", "doe"]).order_by(
                    "name"
                ),
                ["Bar", "Foo"],
                lambda a: a.name,
            )