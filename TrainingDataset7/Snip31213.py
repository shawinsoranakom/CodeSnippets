def test_setdefault(self):
        """
        HttpResponseBase.setdefault() should not change an existing header
        and should be case insensitive.
        """
        r = HttpResponseBase()

        r.headers["Header"] = "Value"
        r.setdefault("header", "changed")
        self.assertEqual(r.headers["header"], "Value")

        r.setdefault("x-header", "DefaultValue")
        self.assertEqual(r.headers["X-Header"], "DefaultValue")