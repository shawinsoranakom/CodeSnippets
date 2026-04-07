def test_annotate_without_default(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.annotate(
                test=Case(
                    When(integer=1, then=1),
                    When(integer=2, then=2),
                )
            ).order_by("pk"),
            [(1, 1), (2, 2), (3, None), (2, 2), (3, None), (3, None), (4, None)],
            transform=attrgetter("integer", "test"),
        )