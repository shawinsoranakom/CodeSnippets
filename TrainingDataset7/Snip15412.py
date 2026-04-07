def test_allvaluesfieldlistfilter_custom_qs(self):
        # Make sure that correct filters are returned with custom querysets
        modeladmin = BookAdminWithCustomQueryset(self.alfred, Book, site)
        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        filterspec = changelist.get_filters(request)[0][0]
        choices = list(filterspec.choices(changelist))
        # Should have 'All', 1999 and 2009 options i.e. the subset of years of
        # books written by alfred (which is the filtering criteria set by
        # BookAdminWithCustomQueryset.get_queryset())
        self.assertEqual(3, len(choices))
        self.assertEqual(choices[0]["query_string"], "?")
        self.assertEqual(choices[1]["query_string"], "?year=1999")
        self.assertEqual(choices[2]["query_string"], "?year=2009")