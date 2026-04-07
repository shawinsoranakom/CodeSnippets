def test_lorem_random(self):
        output = self.engine.render_to_string("lorem_random")
        words = output.split(" ")
        self.assertEqual(len(words), 3)
        for word in words:
            self.assertIn(word, WORDS)