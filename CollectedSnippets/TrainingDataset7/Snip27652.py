def test_multiple_mixed_bases(self):
        A = self.create_model("A", abstract=True)
        M = self.create_model("M")
        P = self.create_model("P")
        Q = self.create_model("Q", bases=(P,), proxy=True)
        Z = self.create_model("Z", bases=(A, M, Q))
        # M has a pointer O2O field p_ptr to P
        self.assertRelated(A, [M, P, Q, Z])
        self.assertRelated(M, [P, Q, Z])
        self.assertRelated(P, [M, Q, Z])
        self.assertRelated(Q, [M, P, Z])
        self.assertRelated(Z, [M, P, Q])