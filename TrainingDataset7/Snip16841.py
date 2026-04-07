def test_get_context_validates_url(self):
        w = widgets.AdminURLFieldWidget()
        for invalid in [
            "",
            "/not/a/full/url/",
            'javascript:alert("Danger XSS!")',
            "http://" + "한.글." * 1_000_000 + "com",
        ]:
            with self.subTest(url=invalid):
                self.assertFalse(w.get_context("name", invalid, {})["url_valid"])
        self.assertTrue(w.get_context("name", "http://example.com", {})["url_valid"])