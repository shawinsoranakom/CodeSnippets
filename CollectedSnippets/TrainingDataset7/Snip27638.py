def test_multiple_nested_bases(self):
        A = self.create_model("A")
        B = self.create_model("B")
        C = self.create_model(
            "C",
            bases=(
                A,
                B,
            ),
        )
        D = self.create_model("D")
        E = self.create_model("E", bases=(D,))
        F = self.create_model(
            "F",
            bases=(
                C,
                E,
            ),
        )
        Y = self.create_model("Y")
        Z = self.create_model("Z", bases=(Y,))
        self.assertRelated(A, [B, C, D, E, F])
        self.assertRelated(B, [A, C, D, E, F])
        self.assertRelated(C, [A, B, D, E, F])
        self.assertRelated(D, [A, B, C, E, F])
        self.assertRelated(E, [A, B, C, D, F])
        self.assertRelated(F, [A, B, C, D, E])
        self.assertRelated(Y, [Z])
        self.assertRelated(Z, [Y])