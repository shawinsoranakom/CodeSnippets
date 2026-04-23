def test_allowed_wildcards(self):
        robotstxt_robotstxt_body = b"""User-agent: first
                                Disallow: /disallowed/*/end$

                                User-agent: second
                                Allow: /*allowed
                                Disallow: /
                                """
        rp = self.parser_cls.from_crawler(
            crawler=None, robotstxt_body=robotstxt_robotstxt_body
        )

        assert rp.allowed("https://www.site.local/disallowed", "first")
        assert not rp.allowed("https://www.site.local/disallowed/xyz/end", "first")
        assert not rp.allowed("https://www.site.local/disallowed/abc/end", "first")
        assert rp.allowed("https://www.site.local/disallowed/xyz/endinglater", "first")

        assert rp.allowed("https://www.site.local/allowed", "second")
        assert rp.allowed("https://www.site.local/is_still_allowed", "second")
        assert rp.allowed("https://www.site.local/is_allowed_too", "second")