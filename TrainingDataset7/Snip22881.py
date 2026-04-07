def test_attribute_class(self):
        class CustomForm(Form):
            default_renderer = CustomRenderer

        form = CustomForm()
        self.assertIsInstance(form.renderer, CustomForm.default_renderer)