def test_empty(self):
        def generator():
            yield from ()

        for choices in ({}, [], (), set(), frozenset(), generator()):
            with self.subTest(choices=choices):
                self.assertEqual(normalize_choices(choices), [])