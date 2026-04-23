def test_AB_ACB(self):
        Q1 = Q(objectb__name="deux")
        Q2 = Q(objectc__objectb__name="deux")
        self.check_union(ObjectA, Q1, Q2)