def test_form_exclude_kwarg_override(self):
        """
        The `exclude` kwarg passed to `ModelAdmin.get_form()` overrides all
        other declarations (#8999).
        """

        class AdminBandForm(forms.ModelForm):
            class Meta:
                model = Band
                exclude = ["name"]

        class BandAdmin(ModelAdmin):
            exclude = ["sign_date"]
            form = AdminBandForm

            def get_form(self, request, obj=None, **kwargs):
                kwargs["exclude"] = ["bio"]
                return super().get_form(request, obj, **kwargs)

        ma = BandAdmin(Band, self.site)
        self.assertEqual(list(ma.get_form(request).base_fields), ["name", "sign_date"])