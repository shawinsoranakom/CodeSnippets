def test_fk_through_proxy(self):
        A = self.create_model("A")
        B = self.create_model("B", bases=(A,), proxy=True)
        C = self.create_model("C", bases=(B,), proxy=True)
        D = self.create_model(
            "D", foreign_keys=[models.ForeignKey("C", models.CASCADE)]
        )
        self.assertRelated(A, [B, C, D])
        self.assertRelated(B, [A, C, D])
        self.assertRelated(C, [A, B, D])
        self.assertRelated(D, [A, B, C])