def test_intermediate_m2m_extern_fk(self):
        A = self.create_model(
            "A", foreign_keys=[models.ManyToManyField("B", through="T")]
        )
        B = self.create_model("B")
        Z = self.create_model("Z")
        T = self.create_model(
            "T",
            foreign_keys=[
                models.ForeignKey("A", models.CASCADE),
                models.ForeignKey("B", models.CASCADE),
                models.ForeignKey("Z", models.CASCADE),
            ],
        )
        self.assertRelated(A, [B, T, Z])
        self.assertRelated(B, [A, T, Z])
        self.assertRelated(T, [A, B, Z])
        self.assertRelated(Z, [A, B, T])