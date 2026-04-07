def test_aggregate_with_expression_as_value(self):
        self.assertEqual(
            CaseTestModel.objects.aggregate(
                one=Sum(Case(When(integer=1, then="integer"))),
                two=Sum(Case(When(integer=2, then=F("integer") - 1))),
                three=Sum(Case(When(integer=3, then=F("integer") + 1))),
            ),
            {"one": 1, "two": 2, "three": 12},
        )