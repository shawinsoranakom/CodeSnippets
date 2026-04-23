def test_covar_pop_sample(self):
        values = StatTestModel.objects.aggregate(
            covarpop=CovarPop(y="int2", x="int1", sample=True)
        )
        self.assertEqual(values, {"covarpop": -1.0})