def test_missing_fields_attribute(self):
        message = (
            "Creating a ModelForm without either the 'fields' attribute "
            "or the 'exclude' attribute is prohibited; form "
            "MissingFieldsForm needs updating."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):

            class MissingFieldsForm(forms.ModelForm):
                class Meta:
                    model = Category