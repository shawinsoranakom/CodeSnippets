def test_lorem1(self):
        output = self.engine.render_to_string("lorem1")
        self.assertEqual(output, "lorem ipsum dolor")