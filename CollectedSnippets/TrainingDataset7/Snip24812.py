def test_header_deletion(self):
        r = HttpResponse("hello")
        r.headers["X-Foo"] = "foo"
        del r.headers["X-Foo"]
        self.assertNotIn("X-Foo", r.headers)
        # del doesn't raise a KeyError on nonexistent headers.
        del r.headers["X-Foo"]