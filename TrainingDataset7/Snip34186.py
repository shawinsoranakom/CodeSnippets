def test_alters_data(self):
        class Doodad:
            alters_data = True

            def __init__(self, value):
                self.num_calls = 0
                self.value = value

            def __call__(self):
                self.num_calls += 1
                return {"the_value": self.value}

        my_doodad = Doodad(42)
        c = Context({"my_doodad": my_doodad})

        # Since ``my_doodad.alters_data`` is True, the template system will not
        # try to call our doodad but will use string_if_invalid
        t = self.engine.from_string("{{ my_doodad.value }}")
        self.assertEqual(t.render(c), "")
        t = self.engine.from_string("{{ my_doodad.the_value }}")
        self.assertEqual(t.render(c), "")

        # Double-check that the object was really never called during the
        # template rendering.
        self.assertEqual(my_doodad.num_calls, 0)