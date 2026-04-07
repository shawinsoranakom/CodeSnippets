def test_attribute_override(self):
        class CustomForm(Form):
            default_renderer = DjangoTemplates()

        custom = CustomRenderer()
        form = CustomForm(renderer=custom)
        self.assertEqual(form.renderer, custom)