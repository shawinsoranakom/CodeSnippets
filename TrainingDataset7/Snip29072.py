def test_custom_form_validation(self):
        # If a form is specified, it should use it allowing custom validation
        # to work properly. This won't break any of the admin widgets or media.
        class AdminBandForm(forms.ModelForm):
            delete = forms.BooleanField()

        class BandAdmin(ModelAdmin):
            form = AdminBandForm

        ma = BandAdmin(Band, self.site)
        self.assertEqual(
            list(ma.get_form(request).base_fields),
            ["name", "bio", "sign_date", "delete"],
        )
        self.assertEqual(
            type(ma.get_form(request).base_fields["sign_date"].widget), AdminDateWidget
        )