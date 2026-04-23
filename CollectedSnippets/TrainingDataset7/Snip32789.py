def test_select_template_empty(self):
        with self.assertRaises(TemplateDoesNotExist):
            select_template([])