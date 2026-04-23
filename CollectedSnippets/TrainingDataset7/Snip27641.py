def test_direct_m2m(self):
        A = self.create_model("A", foreign_keys=[models.ManyToManyField("B")])
        B = self.create_model("B")
        self.assertRelated(A, [A.a_1.rel.through, B])
        self.assertRelated(B, [A, A.a_1.rel.through])