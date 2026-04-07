def test_update_context_manager(self):
        c = Context({"a": 1})
        with c.update({}):
            c["a"] = 2
            self.assertEqual(c["a"], 2)
        self.assertEqual(c["a"], 1)

        with c.update({"a": 3}):
            self.assertEqual(c["a"], 3)
        self.assertEqual(c["a"], 1)