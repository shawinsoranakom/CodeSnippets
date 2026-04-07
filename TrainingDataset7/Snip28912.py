def test_valid_case(self):
        class AdminBandForm(forms.ModelForm):
            delete = forms.BooleanField()

        class BandAdmin(ModelAdmin):
            form = AdminBandForm
            fieldsets = (("Band", {"fields": ("name", "bio", "sign_date", "delete")}),)

        self.assertIsValid(BandAdmin, Band)