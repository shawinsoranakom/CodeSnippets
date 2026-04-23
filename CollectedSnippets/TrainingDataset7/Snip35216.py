def test_transform(self):
        self.assertQuerySetEqual(
            Person.objects.order_by("name"),
            [self.p1.pk, self.p2.pk],
            transform=lambda x: x.pk,
        )