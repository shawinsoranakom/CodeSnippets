def test_default_not_populated_on_optional_checkbox_input(self):
        class PubForm(forms.ModelForm):
            class Meta:
                model = PublicationDefaults
                fields = ("active",)

        # Empty data doesn't use the model default because CheckboxInput
        # doesn't have a value in HTML form submission.
        mf1 = PubForm({})
        self.assertEqual(mf1.errors, {})
        m1 = mf1.save(commit=False)
        self.assertIs(m1.active, False)
        self.assertIsInstance(mf1.fields["active"].widget, forms.CheckboxInput)
        self.assertIs(m1._meta.get_field("active").get_default(), True)