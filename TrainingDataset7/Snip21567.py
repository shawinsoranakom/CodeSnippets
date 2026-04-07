def test_in_subquery(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(
                pk__in=CaseTestModel.objects.annotate(
                    test=Case(
                        When(integer=F("integer2"), then="pk"),
                        When(integer=4, then="pk"),
                    ),
                ).values("test")
            ).order_by("pk"),
            [(1, 1), (2, 2), (3, 3), (4, 5)],
            transform=attrgetter("integer", "integer2"),
        )