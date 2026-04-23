def test_regr_avgy_general(self):
        values = StatTestModel.objects.aggregate(regravgy=RegrAvgY(y="int2", x="int1"))
        self.assertEqual(values, {"regravgy": 2.0})