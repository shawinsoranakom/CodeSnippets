def test_lorem_multiple_paragraphs(self):
        output = self.engine.render_to_string("lorem_multiple_paragraphs")
        self.assertEqual(output.count("<p>"), 2)