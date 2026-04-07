def test_unordered(self):
        self.assertQuerySetEqual(
            Person.objects.order_by("name"), [self.p2, self.p1], ordered=False
        )