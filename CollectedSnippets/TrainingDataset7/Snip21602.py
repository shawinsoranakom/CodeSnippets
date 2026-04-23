def test_update_float(self):
        CaseTestModel.objects.update(
            float=Case(
                When(integer=1, then=1.1),
                When(integer=2, then=2.2),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [(1, 1.1), (2, 2.2), (3, None), (2, 2.2), (3, None), (3, None), (4, None)],
            transform=attrgetter("integer", "float"),
        )