def test_covar_pop_general(self):
        values = StatTestModel.objects.aggregate(covarpop=CovarPop(y="int2", x="int1"))
        self.assertEqual(values, {"covarpop": Approximate(-0.66, places=1)})