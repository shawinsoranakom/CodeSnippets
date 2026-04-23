def test_quote_commas(self):
        """
        #20364 - Check urlize copes with commas following URLs in quotes
        """
        self.assertEqual(
            urlize(
                'Email us at "hi@example.com", or phone us at +xx.yy', autoescape=False
            ),
            'Email us at "<a href="mailto:hi@example.com">hi@example.com</a>", or '
            "phone us at +xx.yy",
        )