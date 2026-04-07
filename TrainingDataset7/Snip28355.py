def test_default_not_populated_on_checkboxselectmultiple(self):
        class PubForm(forms.ModelForm):
            mode = forms.CharField(required=False, widget=forms.CheckboxSelectMultiple)

            class Meta:
                model = PublicationDefaults
                fields = ("mode",)

        # Empty data doesn't use the model default because an unchecked
        # CheckboxSelectMultiple doesn't have a value in HTML form submission.
        mf1 = PubForm({})
        self.assertEqual(mf1.errors, {})
        m1 = mf1.save(commit=False)
        self.assertEqual(m1.mode, "")
        self.assertEqual(m1._meta.get_field("mode").get_default(), "di")