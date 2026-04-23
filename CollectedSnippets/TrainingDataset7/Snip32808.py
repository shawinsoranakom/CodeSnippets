def test_add04(self):
        output = self.engine.render_to_string("add04", {"i": "not_an_int"})
        self.assertEqual(output, "not_an_int16")