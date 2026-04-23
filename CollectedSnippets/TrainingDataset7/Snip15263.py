def test_non_model_fields(self):
        """
        Regression for ensuring ModelAdmin.fields can contain non-model fields
        that broke with r11737
        """

        class SongForm(forms.ModelForm):
            extra_data = forms.CharField()

        class FieldsOnFormOnlyAdmin(admin.ModelAdmin):
            form = SongForm
            fields = ["title", "extra_data"]

        errors = FieldsOnFormOnlyAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])