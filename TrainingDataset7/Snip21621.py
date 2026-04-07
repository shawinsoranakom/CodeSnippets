def test_order_by_conditional_explicit(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(integer__lte=2)
            .annotate(
                test=Case(
                    When(integer=1, then=2),
                    When(integer=2, then=1),
                    default=3,
                )
            )
            .order_by(F("test").asc(), "pk"),
            [(2, 1), (2, 1), (1, 2)],
            transform=attrgetter("integer", "test"),
        )