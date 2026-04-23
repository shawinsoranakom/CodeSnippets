def test_render(self):
        # response is not re-rendered without the render call
        response = self._response().render()
        self.assertEqual(response.content, b"foo")

        # rebaking doesn't change the rendered content
        template = engines["django"].from_string("bar{{ baz }}")
        response.template_name = template
        response.render()
        self.assertEqual(response.content, b"foo")

        # but rendered content can be overridden by manually
        # setting content
        response.content = "bar"
        self.assertEqual(response.content, b"bar")