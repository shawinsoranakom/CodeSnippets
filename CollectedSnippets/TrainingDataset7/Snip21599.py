def test_update_email(self):
        CaseTestModel.objects.update(
            email=Case(
                When(integer=1, then=Value("1@example.com")),
                When(integer=2, then=Value("2@example.com")),
                default=Value(""),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, "1@example.com"),
                (2, "2@example.com"),
                (3, ""),
                (2, "2@example.com"),
                (3, ""),
                (3, ""),
                (4, ""),
            ],
            transform=attrgetter("integer", "email"),
        )