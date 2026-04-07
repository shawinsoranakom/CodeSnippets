def test_regr_sxy_general(self):
        values = StatTestModel.objects.aggregate(regrsxy=RegrSXY(y="int2", x="int1"))
        self.assertEqual(values, {"regrsxy": -2.0})