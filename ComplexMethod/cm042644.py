def test_unicode_url_and_useragent(self):
        robotstxt_robotstxt_body = """
        User-Agent: *
        Disallow: /admin/
        Disallow: /static/
        # taken from https://en.wikipedia.org/robots.txt
        Disallow: /wiki/K%C3%A4ytt%C3%A4j%C3%A4:
        Disallow: /wiki/Käyttäjä:

        User-Agent: UnicödeBöt
        Disallow: /some/randome/page.html""".encode()
        rp = self.parser_cls.from_crawler(
            crawler=None, robotstxt_body=robotstxt_robotstxt_body
        )
        assert rp.allowed("https://site.local/", "*")
        assert not rp.allowed("https://site.local/admin/", "*")
        assert not rp.allowed("https://site.local/static/", "*")
        assert rp.allowed("https://site.local/admin/", "UnicödeBöt")
        assert not rp.allowed("https://site.local/wiki/K%C3%A4ytt%C3%A4j%C3%A4:", "*")
        assert not rp.allowed("https://site.local/wiki/Käyttäjä:", "*")
        assert rp.allowed("https://site.local/some/randome/page.html", "*")
        assert not rp.allowed("https://site.local/some/randome/page.html", "UnicödeBöt")