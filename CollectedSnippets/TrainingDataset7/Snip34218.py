def test_flatten_context_with_context_copy(self):
        ctx1 = Context({"a": 2})
        ctx2 = ctx1.new(Context({"b": 4}))
        self.assertEqual(
            ctx2.dicts, [{"True": True, "False": False, "None": None}, {"b": 4}]
        )
        self.assertEqual(
            ctx2.flatten(),
            {"False": False, "None": None, "True": True, "b": 4},
        )