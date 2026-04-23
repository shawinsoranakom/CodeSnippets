def test_emptylistfieldfilter_invalid_lookup_parameters(self):
        modeladmin = BookAdminWithEmptyFieldListFilter(Book, site)
        request = self.request_factory.get("/", {"author__isempty": 42})
        request.user = self.alfred
        with self.assertRaises(IncorrectLookupParameters):
            modeladmin.get_changelist_instance(request)