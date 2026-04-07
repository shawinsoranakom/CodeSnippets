def test_multiple_bases(self):
        A = self.create_model("A")
        B = self.create_model("B")
        C = self.create_model(
            "C",
            bases=(
                A,
                B,
            ),
        )
        self.assertRelated(A, [B, C])
        self.assertRelated(B, [A, C])
        self.assertRelated(C, [A, B])