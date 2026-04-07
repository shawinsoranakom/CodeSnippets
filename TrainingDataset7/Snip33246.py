def test_autoescape(self):
        self.assertEqual(
            urlizetrunc('foo<a href=" google.com ">bar</a>buz', 10),
            'foo&lt;a href=&quot; <a href="https://google.com" rel="nofollow">'
            "google.com</a> &quot;&gt;bar&lt;/a&gt;buz",
        )