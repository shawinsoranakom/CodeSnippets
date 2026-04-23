def test_push_context_manager(self):
        c = Context({"a": 1})
        with c.push():
            c["a"] = 2
            self.assertEqual(c["a"], 2)
        self.assertEqual(c["a"], 1)

        with c.push(a=3):
            self.assertEqual(c["a"], 3)
        self.assertEqual(c["a"], 1)