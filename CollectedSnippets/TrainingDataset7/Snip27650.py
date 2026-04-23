def test_proxy_base(self):
        A = self.create_model("A")
        B = self.create_model("B", bases=(A,), proxy=True)
        self.assertRelated(A, [B])
        self.assertRelated(B, [])