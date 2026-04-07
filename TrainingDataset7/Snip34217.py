def test_flatten_context_with_context(self):
        """
        Context.push() with a Context argument should work.
        """
        a = Context({"a": 2})
        a.push(Context({"z": "8"}))
        self.assertEqual(
            a.flatten(),
            {
                "False": False,
                "None": None,
                "True": True,
                "a": 2,
                "z": "8",
            },
        )