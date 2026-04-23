def test_flatten_context(self):
        a = Context()
        a.update({"a": 2})
        a.update({"b": 4})
        a.update({"c": 8})

        self.assertEqual(
            a.flatten(),
            {"False": False, "None": None, "True": True, "a": 2, "b": 4, "c": 8},
        )