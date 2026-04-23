def test_render_to_string_with_list_tries_all_engines_before_names(self):
        content = render_to_string(
            ["template_loader/goodbye.html", "template_loader/hello.html"]
        )
        self.assertEqual(content, "Goodbye! (Django templates)\n")