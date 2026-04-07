def test_urlize05(self):
        output = self.engine.render_to_string(
            "urlize05", {"a": "<script>alert('foo')</script>"}
        )
        self.assertEqual(output, "<script>alert('foo')</script>")