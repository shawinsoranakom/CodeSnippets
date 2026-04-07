def test_autoescape_off(self):
        self.assertEqual(
            urlizetrunc('foo<a href=" google.com ">bar</a>buz', 9, autoescape=False),
            'foo<a href=" <a href="https://google.com" rel="nofollow">google.c…</a> ">'
            "bar</a>buz",
        )