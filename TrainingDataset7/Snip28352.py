def test_default_populated_on_optional_field(self):
        class PubForm(forms.ModelForm):
            mode = forms.CharField(max_length=255, required=False)

            class Meta:
                model = PublicationDefaults
                fields = ("mode",)

        # Empty data uses the model field default.
        mf1 = PubForm({})
        self.assertEqual(mf1.errors, {})
        m1 = mf1.save(commit=False)
        self.assertEqual(m1.mode, "di")
        self.assertEqual(m1._meta.get_field("mode").get_default(), "di")

        # Blank data doesn't use the model field default.
        mf2 = PubForm({"mode": ""})
        self.assertEqual(mf2.errors, {})
        m2 = mf2.save(commit=False)
        self.assertEqual(m2.mode, "")