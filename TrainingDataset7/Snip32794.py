def test_render_to_string_second_engine(self):
        content = render_to_string("template_loader/goodbye.html")
        self.assertEqual(content, "Goodbye! (Django templates)\n")