def test_fieldlistfilter_underscorelookup_tuple(self):
        """
        Ensure ('fieldpath', ClassName ) lookups pass lookup_allowed checks
        when fieldpath contains double underscore in value (#19182).
        """
        modeladmin = BookAdminWithUnderscoreLookupAndTuple(Book, site)
        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        request = self.request_factory.get("/", {"author__email": "alfred@example.com"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.bio_book, self.djangonaut_book])