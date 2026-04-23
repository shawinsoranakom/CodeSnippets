def test_push_proper_layering(self):
        c = Context({"a": 1})
        c.push(Context({"b": 2}))
        c.push(Context({"c": 3, "d": {"z": "26"}}))
        self.assertEqual(
            c.dicts,
            [
                {"False": False, "None": None, "True": True},
                {"a": 1},
                {"b": 2},
                {"c": 3, "d": {"z": "26"}},
            ],
        )