def test_empty_fields_on_modelform(self):
        """
        No fields on a ModelForm should actually result in no fields.
        """

        class EmptyPersonForm(forms.ModelForm):
            class Meta:
                model = Person
                fields = ()

        form = EmptyPersonForm()
        self.assertEqual(len(form.fields), 0)