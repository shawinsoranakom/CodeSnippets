def test_extra_field_model_form(self):
        with self.assertRaisesMessage(FieldError, "no-field"):

            class ExtraPersonForm(forms.ModelForm):
                """ModelForm with an extra field"""

                age = forms.IntegerField()

                class Meta:
                    model = Person
                    fields = ("name", "no-field")