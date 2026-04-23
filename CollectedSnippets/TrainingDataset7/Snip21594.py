def test_update_boolean(self):
        CaseTestModel.objects.update(
            boolean=Case(
                When(integer=1, then=True),
                When(integer=2, then=True),
                default=False,
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, True),
                (2, True),
                (3, False),
                (2, True),
                (3, False),
                (3, False),
                (4, False),
            ],
            transform=attrgetter("integer", "boolean"),
        )