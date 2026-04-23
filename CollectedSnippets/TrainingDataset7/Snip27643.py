def test_intermediate_m2m_self(self):
        A = self.create_model(
            "A", foreign_keys=[models.ManyToManyField("A", through="T")]
        )
        T = self.create_model(
            "T",
            foreign_keys=[
                models.ForeignKey("A", models.CASCADE),
                models.ForeignKey("A", models.CASCADE),
            ],
        )
        self.assertRelated(A, [T])
        self.assertRelated(T, [A])