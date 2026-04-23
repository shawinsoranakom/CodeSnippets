def test_dict_context(self):
        response = self._response("{{ foo }}{{ processors }}", {"foo": "bar"})
        self.assertEqual(response.context_data, {"foo": "bar"})
        response.render()
        self.assertEqual(response.content, b"bar")