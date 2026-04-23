def test_regr_count_general(self):
        values = StatTestModel.objects.aggregate(
            regrcount=RegrCount(y="int2", x="int1")
        )
        self.assertEqual(values, {"regrcount": 3})