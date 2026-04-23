def test_direct_m2m_self(self):
        A = self.create_model("A", foreign_keys=[models.ManyToManyField("A")])
        self.assertRelated(A, [A.a_1.rel.through])