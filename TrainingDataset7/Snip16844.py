def test_render_quoting(self):
        """
        WARNING: This test doesn't use assertHTMLEqual since it will get rid
        of some escapes which are tested here!
        """
        HREF_RE = re.compile('href="([^"]+)"')
        VALUE_RE = re.compile('value="([^"]+)"')
        TEXT_RE = re.compile("<a[^>]+>([^>]+)</a>")
        w = widgets.AdminURLFieldWidget()
        output = w.render("test", "http://example.com/<sometag>some-text</sometag>")
        self.assertEqual(
            HREF_RE.search(output)[1],
            "http://example.com/%3Csometag%3Esome-text%3C/sometag%3E",
        )
        self.assertEqual(
            TEXT_RE.search(output)[1],
            "http://example.com/&lt;sometag&gt;some-text&lt;/sometag&gt;",
        )
        self.assertEqual(
            VALUE_RE.search(output)[1],
            "http://example.com/&lt;sometag&gt;some-text&lt;/sometag&gt;",
        )
        output = w.render("test", "http://example-äüö.com/<sometag>some-text</sometag>")
        self.assertEqual(
            HREF_RE.search(output)[1],
            "http://example-%C3%A4%C3%BC%C3%B6.com/"
            "%3Csometag%3Esome-text%3C/sometag%3E",
        )
        self.assertEqual(
            TEXT_RE.search(output)[1],
            "http://example-äüö.com/&lt;sometag&gt;some-text&lt;/sometag&gt;",
        )
        self.assertEqual(
            VALUE_RE.search(output)[1],
            "http://example-äüö.com/&lt;sometag&gt;some-text&lt;/sometag&gt;",
        )
        output = w.render(
            "test", 'http://www.example.com/%C3%A4"><script>alert("XSS!")</script>"'
        )
        self.assertEqual(
            HREF_RE.search(output)[1],
            "http://www.example.com/%C3%A4%22%3E%3Cscript%3Ealert(%22XSS!%22)"
            "%3C/script%3E%22",
        )
        self.assertEqual(
            TEXT_RE.search(output)[1],
            "http://www.example.com/%C3%A4&quot;&gt;&lt;script&gt;"
            "alert(&quot;XSS!&quot;)&lt;/script&gt;&quot;",
        )
        self.assertEqual(
            VALUE_RE.search(output)[1],
            "http://www.example.com/%C3%A4&quot;&gt;&lt;script&gt;"
            "alert(&quot;XSS!&quot;)&lt;/script&gt;&quot;",
        )