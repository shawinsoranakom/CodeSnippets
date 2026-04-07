def test_charset_setter(self):
        r = HttpResponseBase()
        r.charset = "utf-8"
        self.assertEqual(r.charset, "utf-8")