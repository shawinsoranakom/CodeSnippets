def test_quotation_marks(self):
        """
        #20364 - Check urlize correctly include quotation marks in links
        """
        self.assertEqual(
            urlize('before "hi@example.com" afterward', autoescape=False),
            'before "<a href="mailto:hi@example.com">hi@example.com</a>" afterward',
        )
        self.assertEqual(
            urlize('before hi@example.com" afterward', autoescape=False),
            'before <a href="mailto:hi@example.com">hi@example.com</a>" afterward',
        )
        self.assertEqual(
            urlize('before "hi@example.com afterward', autoescape=False),
            'before "<a href="mailto:hi@example.com">hi@example.com</a> afterward',
        )
        self.assertEqual(
            urlize("before 'hi@example.com' afterward", autoescape=False),
            "before '<a href=\"mailto:hi@example.com\">hi@example.com</a>' afterward",
        )
        self.assertEqual(
            urlize("before hi@example.com' afterward", autoescape=False),
            'before <a href="mailto:hi@example.com">hi@example.com</a>\' afterward',
        )
        self.assertEqual(
            urlize("before 'hi@example.com afterward", autoescape=False),
            'before \'<a href="mailto:hi@example.com">hi@example.com</a> afterward',
        )