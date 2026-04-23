def test_get_fieldsets(self):
        # get_fieldsets() is called when figuring out form fields (#18681).
        class BandAdmin(ModelAdmin):
            def get_fieldsets(self, request, obj=None):
                return [(None, {"fields": ["name", "bio"]})]

        ma = BandAdmin(Band, self.site)
        form = ma.get_form(None)
        self.assertEqual(form._meta.fields, ["name", "bio"])

        class InlineBandAdmin(TabularInline):
            model = Concert
            fk_name = "main_band"
            can_delete = False

            def get_fieldsets(self, request, obj=None):
                return [(None, {"fields": ["day", "transport"]})]

        ma = InlineBandAdmin(Band, self.site)
        form = ma.get_formset(None).form
        self.assertEqual(form._meta.fields, ["day", "transport"])