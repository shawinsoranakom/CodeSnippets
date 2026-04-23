def test_html_escaping(self):
        template = self.engine.get_template("template_backends/hello.html")
        context = {"name": '<script>alert("XSS!");</script>'}
        content = template.render(context)

        self.assertIn("&lt;script&gt;", content)
        self.assertNotIn("<script>", content)