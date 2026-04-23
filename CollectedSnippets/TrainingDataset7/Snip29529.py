def test_regr_slope_general(self):
        values = StatTestModel.objects.aggregate(
            regrslope=RegrSlope(y="int2", x="int1")
        )
        self.assertEqual(values, {"regrslope": -1})