def test_render_to_string_with_list_empty(self):
        with self.assertRaises(TemplateDoesNotExist):
            render_to_string([])