def test_fieldlistfilter_multiple_invalid_lookup_parameters(self):
        modeladmin = BookAdmin(Book, site)
        request = self.request_factory.get(
            "/", {"author__id__exact": f"{self.alfred.pk},{self.bob.pk}"}
        )
        request.user = self.alfred
        with self.assertRaises(IncorrectLookupParameters):
            modeladmin.get_changelist_instance(request)