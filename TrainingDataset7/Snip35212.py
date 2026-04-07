def test_ordered(self):
        self.assertQuerySetEqual(
            Person.objects.order_by("name"),
            [self.p1, self.p2],
        )