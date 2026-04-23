def test_prefixed_form_with_default_field(self):
        class PubForm(forms.ModelForm):
            prefix = "form-prefix"

            class Meta:
                model = PublicationDefaults
                fields = ("mode",)

        mode = "de"
        self.assertNotEqual(
            mode, PublicationDefaults._meta.get_field("mode").get_default()
        )

        mf1 = PubForm({"form-prefix-mode": mode})
        self.assertEqual(mf1.errors, {})
        m1 = mf1.save(commit=False)
        self.assertEqual(m1.mode, mode)