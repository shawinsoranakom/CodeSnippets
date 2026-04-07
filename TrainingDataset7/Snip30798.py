def test_A_AB2(self):
        Q1 = Q(name="two")
        Q2 = Q(objectb__name="deux", objectb__num=2)
        self.check_union(ObjectA, Q1, Q2)