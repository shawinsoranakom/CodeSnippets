def test_bilateral_order(self):
        with register_lookup(
            models.IntegerField, Mult3BilateralTransform, Div3BilateralTransform
        ):
            a1 = Author.objects.create(name="a1", age=1)
            a2 = Author.objects.create(name="a2", age=2)
            a3 = Author.objects.create(name="a3", age=3)
            a4 = Author.objects.create(name="a4", age=4)
            baseqs = Author.objects.order_by("name")

            # mult3__div3 always leads to 0
            self.assertSequenceEqual(
                baseqs.filter(age__mult3__div3=42), [a1, a2, a3, a4]
            )
            self.assertSequenceEqual(baseqs.filter(age__div3__mult3=42), [a3])