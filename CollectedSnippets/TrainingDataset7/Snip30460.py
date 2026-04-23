def test_expression(self):
        q = Q(name="test")
        self.assertIs(q.check({"name": Lower(Value("TeSt"))}), True)
        self.assertIs(q.check({"name": Value("other")}), False)