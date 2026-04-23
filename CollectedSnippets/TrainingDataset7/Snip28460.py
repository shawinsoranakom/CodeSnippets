def test_baseform_with_widgets_in_meta(self):
        """
        Using base forms with widgets defined in Meta should not raise errors.
        """
        widget = forms.Textarea()

        class BaseForm(forms.ModelForm):
            class Meta:
                model = Person
                widgets = {"name": widget}
                fields = "__all__"

        Form = modelform_factory(Person, form=BaseForm)
        self.assertIsInstance(Form.base_fields["name"].widget, forms.Textarea)