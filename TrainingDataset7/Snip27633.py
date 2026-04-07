def test_two_sided(self):
        A = self.create_model(
            "A", foreign_keys=[models.ForeignKey("B", models.CASCADE)]
        )
        B = self.create_model(
            "B", foreign_keys=[models.ForeignKey("A", models.CASCADE)]
        )
        self.assertRelated(A, [B])
        self.assertRelated(B, [A])