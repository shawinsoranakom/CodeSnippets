def test_context_processors(self):
        request = RequestFactory().get("/")
        template = self.engine.from_string("Static URL: {{ STATIC_URL }}")
        content = template.render(request=request)
        self.assertEqual(content, "Static URL: /static/")
        with self.settings(STATIC_URL="/s/"):
            content = template.render(request=request)
        self.assertEqual(content, "Static URL: /s/")