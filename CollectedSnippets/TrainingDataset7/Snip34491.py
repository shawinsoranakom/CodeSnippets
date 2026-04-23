def test_render_with_requestcontext(self):
        response = self._response("{{ foo }}{{ processors }}", {"foo": "bar"}).render()
        self.assertEqual(response.content, b"baryes")