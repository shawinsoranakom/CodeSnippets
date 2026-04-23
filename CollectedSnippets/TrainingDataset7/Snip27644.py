def test_intermediate_m2m(self):
        A = self.create_model(
            "A", foreign_keys=[models.ManyToManyField("B", through="T")]
        )
        B = self.create_model("B")
        T = self.create_model(
            "T",
            foreign_keys=[
                models.ForeignKey("A", models.CASCADE),
                models.ForeignKey("B", models.CASCADE),
            ],
        )
        self.assertRelated(A, [B, T])
        self.assertRelated(B, [A, T])
        self.assertRelated(T, [A, B])