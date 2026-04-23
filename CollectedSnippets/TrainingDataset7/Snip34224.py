def test_set_upward_with_push_no_match(self):
        """
        The highest context is used if the given key isn't found.
        """
        c = Context({"b": 1})
        c.push({"b": 2})
        c.set_upward("a", 2)
        self.assertEqual(len(c.dicts), 3)
        self.assertEqual(c.dicts[-1]["a"], 2)