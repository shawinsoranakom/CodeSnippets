def test_update_null_boolean(self):
        CaseTestModel.objects.update(
            null_boolean=Case(
                When(integer=1, then=True),
                When(integer=2, then=False),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, True),
                (2, False),
                (3, None),
                (2, False),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "null_boolean"),
        )