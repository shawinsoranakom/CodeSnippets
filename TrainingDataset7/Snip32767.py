def test_non_ascii_characters(self):
        template = self.engine.get_template("template_backends/hello.html")
        content = template.render({"name": "Jérôme"})
        self.assertEqual(content, "Hello Jérôme!\n")