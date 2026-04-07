def test_file_path_field_blank(self):
        """FilePathField(blank=True) includes the empty option."""

        class FPForm(forms.ModelForm):
            class Meta:
                model = FilePathModel
                fields = "__all__"

        form = FPForm()
        self.assertEqual(
            [name for _, name in form["path"].field.choices], ["---------", "models.py"]
        )