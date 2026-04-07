def test_base(self):
        A = self.create_model("A")
        B = self.create_model("B", bases=(A,))
        self.assertRelated(A, [B])
        self.assertRelated(B, [A])