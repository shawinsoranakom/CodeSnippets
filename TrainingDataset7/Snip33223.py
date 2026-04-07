def test_uppercase(self):
        """
        #18071 - Check urlize accepts uppercased URL schemes
        """
        self.assertEqual(
            urlize("HTTPS://github.com/"),
            '<a href="https://github.com/" rel="nofollow">HTTPS://github.com/</a>',
        )