def test_regr_avgx_general(self):
        values = StatTestModel.objects.aggregate(regravgx=RegrAvgX(y="int2", x="int1"))
        self.assertEqual(values, {"regravgx": 2.0})