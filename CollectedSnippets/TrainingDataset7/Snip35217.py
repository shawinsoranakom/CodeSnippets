def test_repr_transform(self):
        self.assertQuerySetEqual(
            Person.objects.order_by("name"),
            [repr(self.p1), repr(self.p2)],
            transform=repr,
        )