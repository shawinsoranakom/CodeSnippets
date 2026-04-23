def verify_booleanfieldlistfilter_choices(self, modeladmin):
        # False.
        request = self.request_factory.get("/", {"availability__exact": 0})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.bio_book])
        filterspec = changelist.get_filters(request)[0][6]
        self.assertEqual(filterspec.title, "availability")
        choice = select_by(filterspec.choices(changelist), "display", "Paid")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?availability__exact=0")
        # True.
        request = self.request_factory.get("/", {"availability__exact": 1})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.django_book, self.djangonaut_book])
        filterspec = changelist.get_filters(request)[0][6]
        self.assertEqual(filterspec.title, "availability")
        choice = select_by(filterspec.choices(changelist), "display", "Free")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?availability__exact=1")
        # None.
        request = self.request_factory.get("/", {"availability__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.guitar_book])
        filterspec = changelist.get_filters(request)[0][6]
        self.assertEqual(filterspec.title, "availability")
        choice = select_by(filterspec.choices(changelist), "display", "Obscure")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?availability__isnull=True")
        # All.
        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertEqual(
            list(queryset),
            [self.guitar_book, self.django_book, self.bio_book, self.djangonaut_book],
        )
        filterspec = changelist.get_filters(request)[0][6]
        self.assertEqual(filterspec.title, "availability")
        choice = select_by(filterspec.choices(changelist), "display", "All")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?")