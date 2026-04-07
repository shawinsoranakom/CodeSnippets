def test_allvaluesfieldlistfilter(self):
        modeladmin = BookAdmin(Book, site)

        request = self.request_factory.get("/", {"year__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.django_book])

        # Make sure the last choice is None and is selected
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "year")
        choices = list(filterspec.choices(changelist))
        self.assertIs(choices[-1]["selected"], True)
        self.assertEqual(choices[-1]["query_string"], "?year__isnull=True")

        request = self.request_factory.get("/", {"year": "2002"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "year")
        choices = list(filterspec.choices(changelist))
        self.assertIs(choices[2]["selected"], True)
        self.assertEqual(choices[2]["query_string"], "?year=2002")