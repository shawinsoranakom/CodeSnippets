def test_relatedfieldlistfilter_reverse_relationships(self):
        modeladmin = CustomUserAdmin(User, site)

        # FK relationship -----
        request = self.request_factory.get("/", {"books_authored__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.lisa])

        # Make sure the last choice is None and is selected
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "book")
        choices = list(filterspec.choices(changelist))
        self.assertIs(choices[-1]["selected"], True)
        self.assertEqual(choices[-1]["query_string"], "?books_authored__isnull=True")

        request = self.request_factory.get(
            "/", {"books_authored__id__exact": self.bio_book.pk}
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "book")
        choice = select_by(
            filterspec.choices(changelist), "display", self.bio_book.title
        )
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"], "?books_authored__id__exact=%s" % self.bio_book.pk
        )

        # M2M relationship -----
        request = self.request_factory.get("/", {"books_contributed__isnull": "True"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.alfred])

        # Make sure the last choice is None and is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "book")
        choices = list(filterspec.choices(changelist))
        self.assertIs(choices[-1]["selected"], True)
        self.assertEqual(choices[-1]["query_string"], "?books_contributed__isnull=True")

        request = self.request_factory.get(
            "/", {"books_contributed__id__exact": self.django_book.pk}
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "book")
        choice = select_by(
            filterspec.choices(changelist), "display", self.django_book.title
        )
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"],
            "?books_contributed__id__exact=%s" % self.django_book.pk,
        )

        # With one book, the list filter should appear because there is also a
        # (None) option.
        Book.objects.exclude(pk=self.djangonaut_book.pk).delete()
        filterspec = changelist.get_filters(request)[0]
        self.assertEqual(len(filterspec), 2)
        # With no books remaining, no list filters should appear.
        Book.objects.all().delete()
        filterspec = changelist.get_filters(request)[0]
        self.assertEqual(len(filterspec), 0)