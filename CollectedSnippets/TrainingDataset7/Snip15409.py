def test_datefieldlistfilter(self):
        modeladmin = BookAdmin(Book, site)

        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist(request)

        request = self.request_factory.get(
            "/",
            {"date_registered__gte": self.today, "date_registered__lt": self.tomorrow},
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.django_book, self.djangonaut_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][4]
        self.assertEqual(filterspec.title, "date registered")
        choice = select_by(filterspec.choices(changelist), "display", "Today")
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"],
            "?date_registered__gte=%s&date_registered__lt=%s"
            % (
                self.today,
                self.tomorrow,
            ),
        )

        request = self.request_factory.get(
            "/",
            {
                "date_registered__gte": self.today.replace(day=1),
                "date_registered__lt": self.next_month,
            },
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        if (self.today.year, self.today.month) == (
            self.one_week_ago.year,
            self.one_week_ago.month,
        ):
            # In case one week ago is in the same month.
            self.assertEqual(
                list(queryset),
                [self.guitar_book, self.django_book, self.djangonaut_book],
            )
        else:
            self.assertEqual(list(queryset), [self.django_book, self.djangonaut_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][4]
        self.assertEqual(filterspec.title, "date registered")
        choice = select_by(filterspec.choices(changelist), "display", "This month")
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"],
            "?date_registered__gte=%s&date_registered__lt=%s"
            % (
                self.today.replace(day=1),
                self.next_month,
            ),
        )

        request = self.request_factory.get(
            "/",
            {
                "date_registered__gte": self.today.replace(month=1, day=1),
                "date_registered__lt": self.next_year,
            },
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        if self.today.year == self.one_week_ago.year:
            # In case one week ago is in the same year.
            self.assertEqual(
                list(queryset),
                [self.guitar_book, self.django_book, self.djangonaut_book],
            )
        else:
            self.assertEqual(list(queryset), [self.django_book, self.djangonaut_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][4]
        self.assertEqual(filterspec.title, "date registered")
        choice = select_by(filterspec.choices(changelist), "display", "This year")
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"],
            "?date_registered__gte=%s&date_registered__lt=%s"
            % (
                self.today.replace(month=1, day=1),
                self.next_year,
            ),
        )

        request = self.request_factory.get(
            "/",
            {
                "date_registered__gte": str(self.one_week_ago),
                "date_registered__lt": str(self.tomorrow),
            },
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(
            list(queryset), [self.guitar_book, self.django_book, self.djangonaut_book]
        )

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][4]
        self.assertEqual(filterspec.title, "date registered")
        choice = select_by(filterspec.choices(changelist), "display", "Past 7 days")
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"],
            "?date_registered__gte=%s&date_registered__lt=%s"
            % (
                str(self.one_week_ago),
                str(self.tomorrow),
            ),
        )

        # Null/not null queries
        request = self.request_factory.get("/", {"date_registered__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0], self.bio_book)

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][4]
        self.assertEqual(filterspec.title, "date registered")
        choice = select_by(filterspec.choices(changelist), "display", "No date")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?date_registered__isnull=True")

        request = self.request_factory.get("/", {"date_registered__isnull": "False"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(queryset.count(), 3)
        self.assertEqual(
            list(queryset), [self.guitar_book, self.django_book, self.djangonaut_book]
        )

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][4]
        self.assertEqual(filterspec.title, "date registered")
        choice = select_by(filterspec.choices(changelist), "display", "Has date")
        self.assertIs(choice["selected"], True)
        self.assertEqual(choice["query_string"], "?date_registered__isnull=False")