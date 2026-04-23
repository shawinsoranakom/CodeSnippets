def test_brackets(self):
        """
        #19070 - Check urlize handles brackets properly
        """
        self.assertEqual(
            urlize("[see www.example.com]"),
            '[see <a href="https://www.example.com" rel="nofollow">'
            "www.example.com</a>]",
        )
        self.assertEqual(
            urlize("see test[at[example.com"),  # Invalid hostname.
            "see test[at[example.com",
        )
        self.assertEqual(
            urlize("[http://168.192.0.1](http://168.192.0.1)"),
            '[<a href="http://168.192.0.1](http://168.192.0.1)" rel="nofollow">'
            "http://168.192.0.1](http://168.192.0.1)</a>",
        )