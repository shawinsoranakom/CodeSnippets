def test_urlize(self):
        tests = (
            (
                "Search for google.com/?q=! and see.",
                'Search for <a href="https://google.com/?q=">google.com/?q=</a>! and '
                "see.",
            ),
            (
                "Search for google.com/?q=1&lt! and see.",
                'Search for <a href="https://google.com/?q=1%3C">google.com/?q=1&lt'
                "</a>! and see.",
            ),
            (
                lazystr("Search for google.com/?q=!"),
                'Search for <a href="https://google.com/?q=">google.com/?q=</a>!',
            ),
            (
                "http://www.foo.bar/",
                '<a href="http://www.foo.bar/">http://www.foo.bar/</a>',
            ),
            (
                "Look on www.نامه‌ای.com.",
                "Look on <a "
                'href="https://www.%D9%86%D8%A7%D9%85%D9%87%E2%80%8C%D8%A7%DB%8C.com"'
                ">www.نامه‌ای.com</a>.",
            ),
            ("foo@example.com", '<a href="mailto:foo@example.com">foo@example.com</a>'),
            (
                "test@" + "한.글." * 15 + "aaa",
                '<a href="mailto:test@'
                + "%ED%95%9C.%EA%B8%80." * 15
                + 'aaa">'
                + "test@"
                + "한.글." * 15
                + "aaa</a>",
            ),
            (
                # RFC 6068 requires a mailto URI to percent-encode a number of
                # characters that can appear in <addr-spec>.
                "yes+this=is&a%valid!email@example.com",
                '<a href="mailto:yes%2Bthis%3Dis%26a%25valid%21email@example.com"'
                ">yes+this=is&a%valid!email@example.com</a>",
            ),
            (
                "foo@faß.example.com",
                '<a href="mailto:foo@fa%C3%9F.example.com">foo@faß.example.com</a>',
            ),
            (
                "idna-2008@މިހާރު.example.mv",
                '<a href="mailto:idna-2008@%DE%89%DE%A8%DE%80%DE%A7%DE%83%DE%AA.ex'
                'ample.mv">idna-2008@މިހާރު.example.mv</a>',
            ),
            (
                "host.djangoproject.com",
                '<a href="https://host.djangoproject.com">host.djangoproject.com</a>',
            ),
        )
        for value, output in tests:
            with self.subTest(value=value):
                self.assertEqual(urlize(value), output)