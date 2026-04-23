def test_aggregate_with_expression_as_condition(self):
        self.assertEqual(
            CaseTestModel.objects.aggregate(
                equal=Sum(
                    Case(
                        When(integer2=F("integer"), then=1),
                    )
                ),
                plus_one=Sum(
                    Case(
                        When(integer2=F("integer") + 1, then=1),
                    )
                ),
            ),
            {"equal": 3, "plus_one": 4},
        )