def test_render_to_string_with_list_using_engine(self):
        content = render_to_string(
            ["template_loader/unknown.html", "template_loader/hello.html"],
            using="django",
        )
        self.assertEqual(content, "Hello! (Django templates)\n")