def test_autoescape(self):
        self.assertEqual(
            urlize('foo<a href=" google.com ">bar</a>buz'),
            'foo&lt;a href=&quot; <a href="https://google.com" rel="nofollow">'
            "google.com</a> &quot;&gt;bar&lt;/a&gt;buz",
        )