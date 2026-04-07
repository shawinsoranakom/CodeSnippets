def test_fieldsets_with_custom_form_validation(self):
        class BandAdmin(ModelAdmin):
            fieldsets = (("Band", {"fields": ("name",)}),)

        self.assertIsValid(BandAdmin, Band)