def test_autocomplete_e040(self):
        class NoSearchFieldsAdmin(ModelAdmin):
            pass

        class AutocompleteAdmin(ModelAdmin):
            autocomplete_fields = ("featuring",)

        site = AdminSite()
        site.register(Band, NoSearchFieldsAdmin)
        self.assertIsInvalid(
            AutocompleteAdmin,
            Song,
            msg=(
                'NoSearchFieldsAdmin must define "search_fields", because '
                "it's referenced by AutocompleteAdmin.autocomplete_fields."
            ),
            id="admin.E040",
            invalid_obj=AutocompleteAdmin,
            admin_site=site,
        )