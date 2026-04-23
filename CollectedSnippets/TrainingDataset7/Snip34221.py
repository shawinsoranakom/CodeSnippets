def test_set_upward(self):
        c = Context({"a": 1})
        c.set_upward("a", 2)
        self.assertEqual(c.get("a"), 2)