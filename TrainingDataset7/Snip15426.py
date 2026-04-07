def test_relatedonlyfieldlistfilter_manytomany(self):
        modeladmin = BookAdminRelatedOnlyFilter(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure that only actual contributors are present in contrib's list
        # filter
        filterspec = changelist.get_filters(request)[0][5]
        expected = [(self.bob.pk, "bob"), (self.lisa.pk, "lisa")]
        self.assertEqual(sorted(filterspec.lookup_choices), sorted(expected))