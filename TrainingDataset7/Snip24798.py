def test_headers_type(self):
        r = HttpResponse()

        # ASCII strings or bytes values are converted to strings.
        r.headers["key"] = "test"
        self.assertEqual(r.headers["key"], "test")
        r.headers["key"] = b"test"
        self.assertEqual(r.headers["key"], "test")
        self.assertIn(b"test", r.serialize_headers())

        # Non-ASCII values are serialized to Latin-1.
        r.headers["key"] = "café"
        self.assertIn("café".encode("latin-1"), r.serialize_headers())

        # Other Unicode values are MIME-encoded (there's no way to pass them as
        # bytes).
        r.headers["key"] = "†"
        self.assertEqual(r.headers["key"], "=?utf-8?b?4oCg?=")
        self.assertIn(b"=?utf-8?b?4oCg?=", r.serialize_headers())

        # The response also converts string or bytes keys to strings, but
        # requires them to contain ASCII
        r = HttpResponse()
        del r.headers["Content-Type"]
        r.headers["foo"] = "bar"
        headers = list(r.headers.items())
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], ("foo", "bar"))

        r = HttpResponse()
        del r.headers["Content-Type"]
        r.headers[b"foo"] = "bar"
        headers = list(r.headers.items())
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], ("foo", "bar"))
        self.assertIsInstance(headers[0][0], str)

        r = HttpResponse()
        with self.assertRaises(UnicodeError):
            r.headers.__setitem__("føø", "bar")
        with self.assertRaises(UnicodeError):
            r.headers.__setitem__("føø".encode(), "bar")