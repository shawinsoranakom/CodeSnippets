def test_update_with_expression_as_condition(self):
        CaseTestModel.objects.update(
            string=Case(
                When(integer2=F("integer"), then=Value("equal")),
                When(integer2=F("integer") + 1, then=Value("+1")),
            ),
        )
        self.assertQuerySetEqual(
            CaseTestModel.objects.order_by("pk"),
            [
                (1, "equal"),
                (2, "+1"),
                (3, "+1"),
                (2, "equal"),
                (3, "+1"),
                (3, "equal"),
                (4, "+1"),
            ],
            transform=attrgetter("integer", "string"),
        )