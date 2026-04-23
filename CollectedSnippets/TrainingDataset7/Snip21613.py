def test_update_time(self):
        CaseTestModel.objects.update(
            time=Case(
                When(integer=1, then=time(1)),
                When(integer=2, then=time(2)),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, time(1)),
                (2, time(2)),
                (3, None),
                (2, time(2)),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "time"),
        )