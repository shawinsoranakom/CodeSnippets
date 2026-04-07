def test_BAB_BAC(self):
        Q1 = Q(objecta__objectb__name="deux")
        Q2 = Q(objecta__objectc__name="ein")
        self.check_union(ObjectB, Q1, Q2)