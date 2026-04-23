def test_facets_filter(self):
        modeladmin = DecadeFilterBookAdmin(Book, site)
        request = self.request_factory.get(
            "/", {"author__id__exact": self.alfred.pk, "_facets": ""}
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertSequenceEqual(
            queryset,
            list(Book.objects.filter(author=self.alfred).order_by("-id")),
        )
        filters = changelist.get_filters(request)[0]

        tests = [
            # RelatedFieldListFilter.
            ["All", "alfred (2)", "bob (1)", "lisa (0)", "??? (1)"],
            # SimpleListFilter.
            [
                "All",
                "the 1980's (0)",
                "the 1990's (1)",
                "the 2000's (1)",
                "other decades (-)",
            ],
            # BooleanFieldListFilter.
            ["All", "Yes (1)", "No (1)", "Unknown (0)"],
            # ChoicesFieldListFilter.
            [
                "All",
                "Non-Fictional (1)",
                "Fictional (1)",
                "We don't know (0)",
                "Not categorized (0)",
            ],
            # DateFieldListFilter.
            [
                "Any date (2)",
                "Today (1)",
                "Past 7 days (1)",
                "This month (1)",
                "This year (1)",
                "No date (1)",
                "Has date (1)",
            ],
            # AllValuesFieldListFilter.
            [
                "All",
                "alfred@example.com (2)",
                "bob@example.com (0)",
                "lisa@example.com (0)",
            ],
            # RelatedOnlyFieldListFilter.
            ["All", "bob (0)", "lisa (0)", "??? (2)"],
            # EmptyFieldListFilter.
            ["All", "Empty (0)", "Not empty (2)"],
            # SimpleListFilter with join relations.
            ["All", "Owned by Dev Department (2)", "Other (0)"],
        ]
        for filterspec, expected_displays in zip(filters, tests, strict=True):
            with self.subTest(filterspec.__class__.__name__):
                choices = list(filterspec.choices(changelist))
                self.assertChoicesDisplay(choices, expected_displays)
                for choice in choices:
                    self.assertIn("_facets", choice["query_string"])