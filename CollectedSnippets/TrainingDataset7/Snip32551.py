def test_template_tag_escapes(self):
        """
        Storage.url() should return an encoded path and might be overridden
        to also include a querystring. {% static %} escapes the URL to avoid
        raw '&', for example.
        """
        self.assertStaticRenders("a.html", "a.html?a=b&amp;c=d")
        self.assertStaticRenders("a.html", "a.html?a=b&c=d", autoescape=False)