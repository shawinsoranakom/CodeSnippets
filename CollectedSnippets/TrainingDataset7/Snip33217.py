def test_parenthesis_and_bracket(self):
        self.assertEqual(
            urlize("[(https://en.wikipedia.org/)]"),
            '[(<a href="https://en.wikipedia.org/" '
            'rel="nofollow">https://en.wikipedia.org/</a>)]',
        )