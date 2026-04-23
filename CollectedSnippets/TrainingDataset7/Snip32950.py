def test_unicode(self):
        self.assertEqual(
            force_escape("<some html & special characters > here ĐÅ€£"),
            "&lt;some html &amp; special characters &gt; here \u0110\xc5\u20ac\xa3",
        )