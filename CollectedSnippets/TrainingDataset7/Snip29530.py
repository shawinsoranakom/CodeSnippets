def test_regr_sxx_general(self):
        values = StatTestModel.objects.aggregate(regrsxx=RegrSXX(y="int2", x="int1"))
        self.assertEqual(values, {"regrsxx": 2.0})