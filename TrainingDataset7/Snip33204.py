def test_urlize06(self):
        output = self.engine.render_to_string(
            "urlize06", {"a": "<script>alert('foo')</script>"}
        )
        self.assertEqual(output, "&lt;script&gt;alert(&#x27;foo&#x27;)&lt;/script&gt;")