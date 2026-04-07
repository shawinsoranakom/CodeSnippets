def test_relatedonlyfieldlistfilter_foreignkey(self):
        modeladmin = BookAdminRelatedOnlyFilter(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure that only actual authors are present in author's list
        # filter
        filterspec = changelist.get_filters(request)[0][4]
        expected = [(self.alfred.pk, "alfred"), (self.bob.pk, "bob")]
        self.assertEqual(sorted(filterspec.lookup_choices), sorted(expected))