def test_circle(self):
        A = self.create_model(
            "A", foreign_keys=[models.ForeignKey("B", models.CASCADE)]
        )
        B = self.create_model(
            "B", foreign_keys=[models.ForeignKey("C", models.CASCADE)]
        )
        C = self.create_model(
            "C", foreign_keys=[models.ForeignKey("A", models.CASCADE)]
        )
        self.assertRelated(A, [B, C])
        self.assertRelated(B, [A, C])
        self.assertRelated(C, [A, B])