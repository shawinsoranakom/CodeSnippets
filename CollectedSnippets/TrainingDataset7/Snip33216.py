def test_parenthesis(self):
        """
        #11911 - Check urlize keeps balanced parentheses
        """
        self.assertEqual(
            urlize("https://en.wikipedia.org/wiki/Django_(web_framework)"),
            '<a href="https://en.wikipedia.org/wiki/Django_(web_framework)" '
            'rel="nofollow">https://en.wikipedia.org/wiki/Django_(web_framework)</a>',
        )
        self.assertEqual(
            urlize("(see https://en.wikipedia.org/wiki/Django_(web_framework))"),
            '(see <a href="https://en.wikipedia.org/wiki/Django_(web_framework)" '
            'rel="nofollow">https://en.wikipedia.org/wiki/Django_(web_framework)</a>)',
        )