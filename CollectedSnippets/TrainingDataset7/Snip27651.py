def test_nested_proxy_base(self):
        A = self.create_model("A")
        B = self.create_model("B", bases=(A,), proxy=True)
        C = self.create_model("C", bases=(B,), proxy=True)
        self.assertRelated(A, [B, C])
        self.assertRelated(B, [C])
        self.assertRelated(C, [])