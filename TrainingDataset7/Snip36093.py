def test_empty(self):
        def generator():
            yield from ()

        for choices in ({}, [], (), set(), frozenset(), generator(), None, ""):
            with self.subTest(choices=choices):
                result = flatten_choices(choices)
                self.assertIsInstance(result, collections.abc.Generator)
                self.assertEqual(list(result), [])