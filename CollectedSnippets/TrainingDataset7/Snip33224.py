def test_trailing_period(self):
        """
        #18644 - Check urlize trims trailing period when followed by
        parenthesis
        """
        self.assertEqual(
            urlize("(Go to http://www.example.com/foo.)"),
            '(Go to <a href="http://www.example.com/foo" rel="nofollow">'
            "http://www.example.com/foo</a>.)",
        )