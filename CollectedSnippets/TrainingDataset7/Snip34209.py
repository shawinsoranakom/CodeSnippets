def test_push_context_manager_with_context_object(self):
        c = Context({"a": 1})
        with c.push(Context({"a": 3})):
            self.assertEqual(c["a"], 3)
        self.assertEqual(c["a"], 1)