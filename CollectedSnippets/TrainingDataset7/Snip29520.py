def test_corr_general(self):
        values = StatTestModel.objects.aggregate(corr=Corr(y="int2", x="int1"))
        self.assertEqual(values, {"corr": -1.0})