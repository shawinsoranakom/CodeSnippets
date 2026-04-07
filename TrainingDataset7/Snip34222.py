def test_set_upward_empty_context(self):
        empty_context = Context()
        empty_context.set_upward("a", 1)
        self.assertEqual(empty_context.get("a"), 1)