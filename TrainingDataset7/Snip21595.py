def test_update_date(self):
        CaseTestModel.objects.update(
            date=Case(
                When(integer=1, then=date(2015, 1, 1)),
                When(integer=2, then=date(2015, 1, 2)),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, date(2015, 1, 1)),
                (2, date(2015, 1, 2)),
                (3, None),
                (2, date(2015, 1, 2)),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "date"),
        )