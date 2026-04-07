def test_filter_without_default(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(
                integer2=Case(
                    When(integer=2, then=3),
                    When(integer=3, then=4),
                )
            ).order_by("pk"),
            [(2, 3), (3, 4), (3, 4)],
            transform=attrgetter("integer", "integer2"),
        )