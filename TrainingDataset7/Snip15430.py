def verify_booleanfieldlistfilter(self, modeladmin):
        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        request = self.request_factory.get("/", {"is_best_seller__exact": 0})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.bio_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][3]
        self.assertEqual(filterspec.title, "is best seller")
        choice = select_by(filterspec.choices(changelist), "display", "No")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?is_best_seller__exact=0")

        request = self.request_factory.get("/", {"is_best_seller__exact": 1})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.guitar_book, self.djangonaut_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][3]
        self.assertEqual(filterspec.title, "is best seller")
        choice = select_by(filterspec.choices(changelist), "display", "Yes")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?is_best_seller__exact=1")

        request = self.request_factory.get("/", {"is_best_seller__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.django_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][3]
        self.assertEqual(filterspec.title, "is best seller")
        choice = select_by(filterspec.choices(changelist), "display", "Unknown")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?is_best_seller__isnull=True")