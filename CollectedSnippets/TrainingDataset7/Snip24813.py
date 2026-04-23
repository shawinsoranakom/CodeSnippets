def test_instantiate_with_headers(self):
        r = HttpResponse("hello", headers={"X-Foo": "foo"})
        self.assertEqual(r.headers["X-Foo"], "foo")
        self.assertEqual(r.headers["x-foo"], "foo")