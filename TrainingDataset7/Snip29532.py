def test_regr_syy_general(self):
        values = StatTestModel.objects.aggregate(regrsyy=RegrSYY(y="int2", x="int1"))
        self.assertEqual(values, {"regrsyy": 2.0})