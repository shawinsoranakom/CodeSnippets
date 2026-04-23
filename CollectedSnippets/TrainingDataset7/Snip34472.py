def test_template_resolving(self):
        response = SimpleTemplateResponse("first/test.html")
        response.render()
        self.assertEqual(response.content, b"First template\n")

        templates = ["foo.html", "second/test.html", "first/test.html"]
        response = SimpleTemplateResponse(templates)
        response.render()
        self.assertEqual(response.content, b"Second template\n")

        response = self._response()
        response.render()
        self.assertEqual(response.content, b"foo")