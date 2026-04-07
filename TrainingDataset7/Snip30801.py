def test_BAB_BACB(self):
        Q1 = Q(objecta__objectb__name="deux")
        Q2 = Q(objecta__objectc__objectb__name="trois")
        self.check_union(ObjectB, Q1, Q2)