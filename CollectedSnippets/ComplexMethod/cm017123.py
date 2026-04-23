def _test_facets(self, modeladmin, request, query_string=None):
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)
        self.assertSequenceEqual(queryset, list(Book.objects.order_by("-id")))
        filters = changelist.get_filters(request)[0]
        # Filters for DateFieldListFilter.
        expected_date_filters = ["Any date (4)", "Today (2)", "Past 7 days (3)"]
        if (
            self.today.month == self.one_week_ago.month
            and self.today.year == self.one_week_ago.year
        ):
            expected_date_filters.extend(["This month (3)", "This year (3)"])
        elif self.today.year == self.one_week_ago.year:
            expected_date_filters.extend(["This month (2)", "This year (3)"])
        else:
            expected_date_filters.extend(["This month (2)", "This year (2)"])
        expected_date_filters.extend(["No date (1)", "Has date (3)"])

        empty_choice_count = (
            2 if connection.features.interprets_empty_strings_as_nulls else 1
        )
        tests = [
            # RelatedFieldListFilter.
            ["All", "alfred (2)", "bob (1)", "lisa (0)", "??? (1)"],
            # SimpleListFilter.
            [
                "All",
                "the 1980's (0)",
                "the 1990's (1)",
                "the 2000's (2)",
                "other decades (-)",
            ],
            # BooleanFieldListFilter.
            ["All", "Yes (2)", "No (1)", "Unknown (1)"],
            # ChoicesFieldListFilter.
            [
                "All",
                "Non-Fictional (1)",
                "Fictional (1)",
                f"We don't know ({empty_choice_count})",
                f"Not categorized ({empty_choice_count})",
            ],
            # DateFieldListFilter.
            expected_date_filters,
            # AllValuesFieldListFilter.
            [
                "All",
                "alfred@example.com (2)",
                "bob@example.com (1)",
                "lisa@example.com (0)",
            ],
            # RelatedOnlyFieldListFilter.
            ["All", "bob (1)", "lisa (1)", "??? (3)"],
            # EmptyFieldListFilter.
            ["All", "Empty (2)", "Not empty (2)"],
            # SimpleListFilter with join relations.
            ["All", "Owned by Dev Department (2)", "Other (2)"],
        ]
        for filterspec, expected_displays in zip(filters, tests, strict=True):
            with self.subTest(filterspec.__class__.__name__):
                choices = list(filterspec.choices(changelist))
                self.assertChoicesDisplay(choices, expected_displays)
                if query_string:
                    for choice in choices:
                        self.assertIn(query_string, choice["query_string"])