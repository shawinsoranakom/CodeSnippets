def test_non_model_first_field(self):
        """
        Regression for ensuring ModelAdmin.field can handle first elem being a
        non-model field (test fix for UnboundLocalError introduced with
        r16225).
        """

        class SongForm(forms.ModelForm):
            extra_data = forms.CharField()

            class Meta:
                model = Song
                fields = "__all__"

        class FieldsOnFormOnlyAdmin(admin.ModelAdmin):
            form = SongForm
            fields = ["extra_data", "title"]

        errors = FieldsOnFormOnlyAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])