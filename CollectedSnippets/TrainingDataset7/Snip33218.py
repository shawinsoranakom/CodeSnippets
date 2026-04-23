def test_nofollow(self):
        """
        #12183 - Check urlize adds nofollow properly - see #12183
        """
        self.assertEqual(
            urlize("foo@bar.com or www.bar.com"),
            '<a href="mailto:foo@bar.com">foo@bar.com</a> or '
            '<a href="https://www.bar.com" rel="nofollow">www.bar.com</a>',
        )