def test_value_placeholder_with_file_field(self):
        class MyForm(forms.Form):
            field = forms.FileField(
                validators=[validators.validate_image_file_extension],
                error_messages={"invalid_extension": "%(value)s"},
            )

        form = MyForm(files={"field": SimpleUploadedFile("myfile.txt", b"abc")})
        self.assertIs(form.is_valid(), False)
        self.assertEqual(form.errors, {"field": ["myfile.txt"]})