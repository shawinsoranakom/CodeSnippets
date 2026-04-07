def test_queryset(self):
        self.assertQuerySetEqual(
            Person.objects.order_by("name"),
            Person.objects.order_by("name"),
        )