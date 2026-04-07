def test_lorem_incorrect_count(self):
        output = self.engine.render_to_string("lorem_incorrect_count")
        self.assertEqual(output.count("<p>"), 1)