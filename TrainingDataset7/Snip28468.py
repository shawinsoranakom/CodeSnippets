def test_custom_callback_from_base_form_meta(self):
        def callback(db_field, **kwargs):
            return forms.CharField(widget=forms.Textarea)

        class BaseForm(forms.ModelForm):
            class Meta:
                model = Person
                fields = "__all__"
                formfield_callback = callback

        NewForm = modelform_factory(model=Person, form=BaseForm)

        class InheritedForm(NewForm):
            pass

        for name, field in NewForm.base_fields.items():
            self.assertEqual(type(field.widget), forms.Textarea)
            self.assertEqual(
                type(field.widget),
                type(InheritedForm.base_fields[name].widget),
            )