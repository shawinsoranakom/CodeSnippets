def test_regr_r2_general(self):
        values = StatTestModel.objects.aggregate(regrr2=RegrR2(y="int2", x="int1"))
        self.assertEqual(values, {"regrr2": 1})