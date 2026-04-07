def test_abstract_base(self):
        A = self.create_model("A", abstract=True)
        B = self.create_model("B", bases=(A,))
        self.assertRelated(A, [B])
        self.assertRelated(B, [])