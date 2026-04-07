def test_aggregate(self):
        self.assertEqual(
            CaseTestModel.objects.aggregate(
                one=Sum(
                    Case(
                        When(integer=1, then=1),
                    )
                ),
                two=Sum(
                    Case(
                        When(integer=2, then=1),
                    )
                ),
                three=Sum(
                    Case(
                        When(integer=3, then=1),
                    )
                ),
                four=Sum(
                    Case(
                        When(integer=4, then=1),
                    )
                ),
            ),
            {"one": 1, "two": 2, "three": 3, "four": 1},
        )