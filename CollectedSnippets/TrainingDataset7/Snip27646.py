def test_intermediate_m2m_base(self):
        A = self.create_model(
            "A", foreign_keys=[models.ManyToManyField("B", through="T")]
        )
        B = self.create_model("B")
        S = self.create_model("S")
        T = self.create_model(
            "T",
            foreign_keys=[
                models.ForeignKey("A", models.CASCADE),
                models.ForeignKey("B", models.CASCADE),
            ],
            bases=(S,),
        )
        self.assertRelated(A, [B, S, T])
        self.assertRelated(B, [A, S, T])
        self.assertRelated(S, [A, B, T])
        self.assertRelated(T, [A, B, S])