def test_using(self):
        request = self.factory.get("/")
        response = TemplateResponse(request, "template_tests/using.html").render()
        self.assertEqual(response.content, b"DTL\n")
        response = TemplateResponse(
            request, "template_tests/using.html", using="django"
        ).render()
        self.assertEqual(response.content, b"DTL\n")
        response = TemplateResponse(
            request, "template_tests/using.html", using="jinja2"
        ).render()
        self.assertEqual(response.content, b"Jinja2\n")