def test_render(self):
        response = self._response("{{ foo }}{{ processors }}").render()
        self.assertEqual(response.content, b"yes")