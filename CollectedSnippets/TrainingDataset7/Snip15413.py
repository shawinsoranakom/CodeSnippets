def test_relatedfieldlistfilter_foreignkey(self):
        modeladmin = BookAdmin(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure that all users are present in the author's list filter
        filterspec = changelist.get_filters(request)[0][1]
        expected = [
            (self.alfred.pk, "alfred"),
            (self.bob.pk, "bob"),
            (self.lisa.pk, "lisa"),
        ]
        self.assertEqual(sorted(filterspec.lookup_choices), sorted(expected))

        request = self.request_factory.get("/", {"author__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.guitar_book])

        # Make sure the last choice is None and is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "Verbose Author")
        choices = list(filterspec.choices(changelist))
        self.assertIs(choices[-1]["selected"], True)
        self.assertEqual(choices[-1]["query_string"], "?author__isnull=True")

        request = self.request_factory.get("/", {"author__id__exact": self.alfred.pk})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "Verbose Author")
        # order of choices depends on User model, which has no order
        choice = select_by(filterspec.choices(changelist), "display", "alfred")
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"], "?author__id__exact=%s" % self.alfred.pk
        )