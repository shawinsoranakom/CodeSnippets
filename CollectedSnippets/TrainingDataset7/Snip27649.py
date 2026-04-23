def test_nested_abstract_base(self):
        A = self.create_model("A", abstract=True)
        B = self.create_model("B", bases=(A,), abstract=True)
        C = self.create_model("C", bases=(B,))
        self.assertRelated(A, [B, C])
        self.assertRelated(B, [C])
        self.assertRelated(C, [])