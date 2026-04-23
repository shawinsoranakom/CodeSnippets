def test_update_uuid(self):
        CaseTestModel.objects.update(
            uuid=Case(
                When(integer=1, then=UUID("11111111111111111111111111111111")),
                When(integer=2, then=UUID("22222222222222222222222222222222")),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, UUID("11111111111111111111111111111111")),
                (2, UUID("22222222222222222222222222222222")),
                (3, None),
                (2, UUID("22222222222222222222222222222222")),
                (3, None),
                (3, None),
                (4, None),
            ],
            transform=attrgetter("integer", "uuid"),
        )