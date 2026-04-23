def test_trailing_multiple_punctuation(self):
        self.assertEqual(
            urlize("A test http://testing.com/example.."),
            'A test <a href="http://testing.com/example" rel="nofollow">'
            "http://testing.com/example</a>..",
        )
        self.assertEqual(
            urlize("A test http://testing.com/example!!"),
            'A test <a href="http://testing.com/example" rel="nofollow">'
            "http://testing.com/example</a>!!",
        )
        self.assertEqual(
            urlize("A test http://testing.com/example!!!"),
            'A test <a href="http://testing.com/example" rel="nofollow">'
            "http://testing.com/example</a>!!!",
        )
        self.assertEqual(
            urlize('A test http://testing.com/example.,:;)"!'),
            'A test <a href="http://testing.com/example" rel="nofollow">'
            "http://testing.com/example</a>.,:;)&quot;!",
        )