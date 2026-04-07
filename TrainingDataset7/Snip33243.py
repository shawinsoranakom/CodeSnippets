def test_overtruncate(self):
        self.assertEqual(
            urlizetrunc("http://short.com/", 20),
            '<a href="http://short.com/" rel="nofollow">http://short.com/</a>',
        )