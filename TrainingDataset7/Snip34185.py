def test_callable(self):
        class Doodad:
            def __init__(self, value):
                self.num_calls = 0
                self.value = value

            def __call__(self):
                self.num_calls += 1
                return {"the_value": self.value}

        my_doodad = Doodad(42)
        c = Context({"my_doodad": my_doodad})

        # We can't access ``my_doodad.value`` in the template, because
        # ``my_doodad.__call__`` will be invoked first, yielding a dictionary
        # without a key ``value``.
        t = self.engine.from_string("{{ my_doodad.value }}")
        self.assertEqual(t.render(c), "")

        # We can confirm that the doodad has been called
        self.assertEqual(my_doodad.num_calls, 1)

        # But we can access keys on the dict that's returned
        # by ``__call__``, instead.
        t = self.engine.from_string("{{ my_doodad.the_value }}")
        self.assertEqual(t.render(c), "42")
        self.assertEqual(my_doodad.num_calls, 2)