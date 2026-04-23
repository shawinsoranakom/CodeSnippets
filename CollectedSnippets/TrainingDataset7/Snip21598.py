def test_update_duration(self):
        CaseTestModel.objects.update(
            duration=Case(
                When(integer=1, then=timedelta(1)),
                When(integer=2, then=timedelta(2)),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, timedelta(1)),
                (2, timedelta(2)),
                (3, None),
                (2, timedelta(2)),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "duration"),
        )