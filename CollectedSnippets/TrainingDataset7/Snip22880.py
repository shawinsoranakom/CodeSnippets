def test_attribute_instance(self):
        class CustomForm(Form):
            default_renderer = DjangoTemplates()

        form = CustomForm()
        self.assertEqual(form.renderer, CustomForm.default_renderer)