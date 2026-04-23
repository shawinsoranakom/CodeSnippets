def test_headers(self):
        response = SimpleTemplateResponse(
            "first/test.html",
            {"value": 123, "fn": datetime.now},
            headers={"X-Foo": "foo"},
        )
        self.assertEqual(response.headers["X-Foo"], "foo")