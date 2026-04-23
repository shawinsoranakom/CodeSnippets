def test_default_filefield(self):
        class PubForm(forms.ModelForm):
            class Meta:
                model = PublicationDefaults
                fields = ("file",)

        mf1 = PubForm({})
        self.assertEqual(mf1.errors, {})
        m1 = mf1.save(commit=False)
        self.assertEqual(m1.file.name, "default.txt")

        mf2 = PubForm({}, {"file": SimpleUploadedFile("name", b"foo")})
        self.assertEqual(mf2.errors, {})
        m2 = mf2.save(commit=False)
        self.assertEqual(m2.file.name, "name")