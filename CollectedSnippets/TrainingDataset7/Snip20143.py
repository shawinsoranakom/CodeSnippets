def test_div3_extract(self):
        with register_lookup(models.IntegerField, Div3Transform):
            a1 = Author.objects.create(name="a1", age=1)
            a2 = Author.objects.create(name="a2", age=2)
            a3 = Author.objects.create(name="a3", age=3)
            a4 = Author.objects.create(name="a4", age=4)
            baseqs = Author.objects.order_by("name")
            self.assertSequenceEqual(baseqs.filter(age__div3=2), [a2])
            self.assertSequenceEqual(baseqs.filter(age__div3__lte=3), [a1, a2, a3, a4])
            self.assertSequenceEqual(baseqs.filter(age__div3__in=[0, 2]), [a2, a3])
            self.assertSequenceEqual(baseqs.filter(age__div3__in=[2, 4]), [a2])
            self.assertSequenceEqual(baseqs.filter(age__div3__gte=3), [])
            self.assertSequenceEqual(
                baseqs.filter(age__div3__range=(1, 2)), [a1, a2, a4]
            )