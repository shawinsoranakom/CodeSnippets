def test_facets_disallowed(self):
        modeladmin = DecadeFilterBookAdminDisallowFacets(Book, site)
        # Facets are not visible even when in the url query.
        request = self.request_factory.get("/?_facets")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertSequenceEqual(queryset, list(Book.objects.order_by("-id")))
        filters = changelist.get_filters(request)[0]

        tests = [
            # RelatedFieldListFilter.
            ["All", "alfred", "bob", "lisa", "???"],
            # SimpleListFilter.
            ["All", "the 1980's", "the 1990's", "the 2000's", "other decades"],
            # BooleanFieldListFilter.
            ["All", "Yes", "No", "Unknown"],
            # ChoicesFieldListFilter.
            ["All", "Non-Fictional", "Fictional", "We don't know", "Not categorized"],
            # DateFieldListFilter.
            [
                "Any date",
                "Today",
                "Past 7 days",
                "This month",
                "This year",
                "No date",
                "Has date",
            ],
            # AllValuesFieldListFilter.
            ["All", "alfred@example.com", "bob@example.com", "lisa@example.com"],
            # RelatedOnlyFieldListFilter.
            ["All", "bob", "lisa", "???"],
            # EmptyFieldListFilter.
            ["All", "Empty", "Not empty"],
            # SimpleListFilter with join relations.
            ["All", "Owned by Dev Department", "Other"],
        ]
        for filterspec, expected_displays in zip(filters, tests, strict=True):
            with self.subTest(filterspec.__class__.__name__):
                self.assertChoicesDisplay(
                    filterspec.choices(changelist),
                    expected_displays,
                )