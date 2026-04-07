def test_unrelated(self):
        A = self.create_model("A")
        B = self.create_model("B")
        self.assertRelated(A, [])
        self.assertRelated(B, [])