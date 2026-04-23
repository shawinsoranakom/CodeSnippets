def test_autoescape_off(self):
        self.assertEqual(
            urlize('foo<a href=" google.com ">bar</a>buz', autoescape=False),
            'foo<a href=" <a href="https://google.com" rel="nofollow">google.com</a> ">'
            "bar</a>buz",
        )