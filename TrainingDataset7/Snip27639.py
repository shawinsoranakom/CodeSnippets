def test_base_to_base_fk(self):
        A = self.create_model(
            "A", foreign_keys=[models.ForeignKey("Y", models.CASCADE)]
        )
        B = self.create_model("B", bases=(A,))
        Y = self.create_model("Y")
        Z = self.create_model("Z", bases=(Y,))
        self.assertRelated(A, [B, Y, Z])
        self.assertRelated(B, [A, Y, Z])
        self.assertRelated(Y, [A, B, Z])
        self.assertRelated(Z, [A, B, Y])