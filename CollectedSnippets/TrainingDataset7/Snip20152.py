def test_bilateral_fexpr(self):
        with register_lookup(models.IntegerField, Mult3BilateralTransform):
            a1 = Author.objects.create(name="a1", age=1, average_rating=3.2)
            a2 = Author.objects.create(name="a2", age=2, average_rating=0.5)
            a3 = Author.objects.create(name="a3", age=3, average_rating=1.5)
            a4 = Author.objects.create(name="a4", age=4)
            baseqs = Author.objects.order_by("name")
            self.assertSequenceEqual(
                baseqs.filter(age__mult3=models.F("age")), [a1, a2, a3, a4]
            )
            # Same as age >= average_rating
            self.assertSequenceEqual(
                baseqs.filter(age__mult3__gte=models.F("average_rating")), [a2, a3]
            )