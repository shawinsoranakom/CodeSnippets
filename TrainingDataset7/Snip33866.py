def test_lorem_default(self):
        output = self.engine.render_to_string("lorem_default")
        self.assertEqual(output, COMMON_P)