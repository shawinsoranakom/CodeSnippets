def test_length04(self):
        output = self.engine.render_to_string("length04", {"string": "django"})
        self.assertEqual(output, "6")