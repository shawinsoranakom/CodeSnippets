def test_BA_BCA__BAB_BAC_BCA(self):
        Q1 = Q(objecta__name="one", objectc__objecta__name="two")
        Q2 = Q(
            objecta__objectc__name="ein",
            objectc__objecta__name="three",
            objecta__objectb__name="trois",
        )
        self.check_union(ObjectB, Q1, Q2)