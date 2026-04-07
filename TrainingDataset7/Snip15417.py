def test_relatedfieldlistfilter_manytomany(self):
        modeladmin = BookAdmin(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure that all users are present in the contrib's list filter
        filterspec = changelist.get_filters(request)[0][2]
        expected = [
            (self.alfred.pk, "alfred"),
            (self.bob.pk, "bob"),
            (self.lisa.pk, "lisa"),
        ]
        self.assertEqual(sorted(filterspec.lookup_choices), sorted(expected))

        request = self.request_factory.get("/", {"contributors__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(
            list(queryset), [self.django_book, self.bio_book, self.djangonaut_book]
        )

        # Make sure the last choice is None and is selected
        filterspec = changelist.get_filters(request)[0][2]
        self.assertEqual(filterspec.title, "Verbose Contributors")
        choices = list(filterspec.choices(changelist))
        self.assertIs(choices[-1]["selected"], True)
        self.assertEqual(choices[-1]["query_string"], "?contributors__isnull=True")

        request = self.request_factory.get(
            "/", {"contributors__id__exact": self.bob.pk}
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][2]
        self.assertEqual(filterspec.title, "Verbose Contributors")
        choice = select_by(filterspec.choices(changelist), "display", "bob")
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"], "?contributors__id__exact=%s" % self.bob.pk
        )