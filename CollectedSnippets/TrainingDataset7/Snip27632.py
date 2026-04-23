def test_nested_fk(self):
        A = self.create_model(
            "A", foreign_keys=[models.ForeignKey("B", models.CASCADE)]
        )
        B = self.create_model(
            "B", foreign_keys=[models.ForeignKey("C", models.CASCADE)]
        )
        C = self.create_model("C")
        self.assertRelated(A, [B, C])
        self.assertRelated(B, [A, C])
        self.assertRelated(C, [A, B])