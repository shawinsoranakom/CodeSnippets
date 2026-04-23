def test_autocomplete_is_valid(self):
        class SearchFieldsAdmin(ModelAdmin):
            search_fields = "name"

        class AutocompleteAdmin(ModelAdmin):
            autocomplete_fields = ("featuring",)

        site = AdminSite()
        site.register(Band, SearchFieldsAdmin)
        self.assertIsValid(AutocompleteAdmin, Song, admin_site=site)