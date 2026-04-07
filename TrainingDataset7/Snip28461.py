def test_factory_with_widget_argument(self):
        """Regression for #15315: modelform_factory should accept widgets
        argument
        """
        widget = forms.Textarea()

        # Without a widget should not set the widget to textarea
        Form = modelform_factory(Person, fields="__all__")
        self.assertNotEqual(Form.base_fields["name"].widget.__class__, forms.Textarea)

        # With a widget should not set the widget to textarea
        Form = modelform_factory(Person, fields="__all__", widgets={"name": widget})
        self.assertEqual(Form.base_fields["name"].widget.__class__, forms.Textarea)