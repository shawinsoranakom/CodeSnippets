def test_fieldlistfilter_invalid_lookup_parameters(self):
        """Filtering by an invalid value."""
        modeladmin = BookAdmin(Book, site)
        request = self.request_factory.get(
            "/", {"author__id__exact": "StringNotInteger!"}
        )
        request.user = self.alfred
        with self.assertRaises(IncorrectLookupParameters):
            modeladmin.get_changelist_instance(request)