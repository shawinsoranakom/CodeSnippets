def test_direct_fk(self):
        A = self.create_model(
            "A", foreign_keys=[models.ForeignKey("B", models.CASCADE)]
        )
        B = self.create_model("B")
        self.assertRelated(A, [B])
        self.assertRelated(B, [A])