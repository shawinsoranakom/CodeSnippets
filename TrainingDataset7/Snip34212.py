def test_update_proper_layering(self):
        c = Context({"a": 1})
        c.update(Context({"b": 2}))
        c.update(Context({"c": 3, "d": {"z": "26"}}))
        self.assertEqual(
            c.dicts,
            [
                {"False": False, "None": None, "True": True},
                {"a": 1},
                {"b": 2},
                {"c": 3, "d": {"z": "26"}},
            ],
        )