def test_A_AB(self):
        Q1 = Q(name="two")
        Q2 = Q(objectb__name="deux")
        self.check_union(ObjectA, Q1, Q2)