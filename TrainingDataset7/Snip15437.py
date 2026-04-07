def test_simplelistfilter(self):
        modeladmin = DecadeFilterBookAdmin(Book, site)

        # Make sure that the first option is 'All' ---------------------------
        request = self.request_factory.get("/", {})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), list(Book.objects.order_by("-id")))

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "publication decade")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[0]["display"], "All")
        self.assertIs(choices[0]["selected"], True)
        self.assertEqual(choices[0]["query_string"], "?")

        # Look for books in the 1980s ----------------------------------------
        request = self.request_factory.get("/", {"publication-decade": "the 80s"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "publication decade")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[1]["display"], "the 1980's")
        self.assertIs(choices[1]["selected"], True)
        self.assertEqual(choices[1]["query_string"], "?publication-decade=the+80s")

        # Look for books in the 1990s ----------------------------------------
        request = self.request_factory.get("/", {"publication-decade": "the 90s"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.bio_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "publication decade")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[2]["display"], "the 1990's")
        self.assertIs(choices[2]["selected"], True)
        self.assertEqual(choices[2]["query_string"], "?publication-decade=the+90s")

        # Look for books in the 2000s ----------------------------------------
        request = self.request_factory.get("/", {"publication-decade": "the 00s"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.guitar_book, self.djangonaut_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "publication decade")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[3]["display"], "the 2000's")
        self.assertIs(choices[3]["selected"], True)
        self.assertEqual(choices[3]["query_string"], "?publication-decade=the+00s")

        # Combine multiple filters -------------------------------------------
        request = self.request_factory.get(
            "/", {"publication-decade": "the 00s", "author__id__exact": self.alfred.pk}
        )
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.djangonaut_book])

        # Make sure the correct choices are selected
        filterspec = changelist.get_filters(request)[0][1]
        self.assertEqual(filterspec.title, "publication decade")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[3]["display"], "the 2000's")
        self.assertIs(choices[3]["selected"], True)
        self.assertEqual(
            choices[3]["query_string"],
            "?author__id__exact=%s&publication-decade=the+00s" % self.alfred.pk,
        )

        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "Verbose Author")
        choice = select_by(filterspec.choices(changelist), "display", "alfred")
        self.assertIs(choice["selected"], True)
        self.assertEqual(
            choice["query_string"],
            "?author__id__exact=%s&publication-decade=the+00s" % self.alfred.pk,
        )