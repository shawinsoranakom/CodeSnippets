def test_render_to_string_with_list_first_engine(self):
        content = render_to_string(
            ["template_loader/unknown.html", "template_loader/hello.html"]
        )
        self.assertEqual(content, "Hello! (template strings)\n")