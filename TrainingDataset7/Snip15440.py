def test_simplelistfilter_with_none_returning_lookups(self):
        """
        A SimpleListFilter lookups method can return None but disables the
        filter completely.
        """
        modeladmin = DecadeFilterBookAdminWithNoneReturningLookups(Book, site)
        request = self.request_factory.get("/", {})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0]
        self.assertEqual(len(filterspec), 0)