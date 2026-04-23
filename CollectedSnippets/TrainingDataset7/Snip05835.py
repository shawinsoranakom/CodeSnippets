def autocomplete_view(self, request):
        return AutocompleteJsonView.as_view(admin_site=self)(request)