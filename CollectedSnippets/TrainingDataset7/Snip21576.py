def test_filter_with_expression_as_condition(self):
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(
                string=Case(
                    When(integer2=F("integer"), then=Value("2")),
                    When(integer2=F("integer") + 1, then=Value("3")),
                )
            ).order_by("pk"),
            [(3, 4, "3"), (2, 2, "2"), (3, 4, "3")],
            transform=attrgetter("integer", "integer2", "string"),
        )