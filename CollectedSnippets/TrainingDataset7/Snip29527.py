def test_regr_intercept_general(self):
        values = StatTestModel.objects.aggregate(
            regrintercept=RegrIntercept(y="int2", x="int1")
        )
        self.assertEqual(values, {"regrintercept": 4})