def test_update_date_time(self):
        CaseTestModel.objects.update(
            date_time=Case(
                When(integer=1, then=datetime(2015, 1, 1)),
                When(integer=2, then=datetime(2015, 1, 2)),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, datetime(2015, 1, 1)),
                (2, datetime(2015, 1, 2)),
                (3, None),
                (2, datetime(2015, 1, 2)),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "date_time"),
        )