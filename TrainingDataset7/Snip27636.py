def test_nested_base(self):
        A = self.create_model("A")
        B = self.create_model("B", bases=(A,))
        C = self.create_model("C", bases=(B,))
        self.assertRelated(A, [B, C])
        self.assertRelated(B, [A, C])
        self.assertRelated(C, [A, B])