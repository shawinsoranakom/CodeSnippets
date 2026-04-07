def test_parameter_ends_with__in__or__isnull(self):
        """
        A SimpleListFilter's parameter name is not mistaken for a model field
        if it ends with '__isnull' or '__in' (#17091).
        """
        # When it ends with '__in' -----------------------------------------
        modeladmin = DecadeFilterBookAdminParameterEndsWith__In(Book, site)
        request = self.request_factory.get("/", {"decade__in": "the 90s"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.bio_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "publication decade")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[2]["display"], "the 1990's")
        self.assertIs(choices[2]["selected"], True)
        self.assertEqual(choices[2]["query_string"], "?decade__in=the+90s")

        # When it ends with '__isnull' ---------------------------------------
        modeladmin = DecadeFilterBookAdminParameterEndsWith__Isnull(Book, site)
        request = self.request_factory.get("/", {"decade__isnull": "the 90s"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.bio_book])

        # Make sure the correct choice is selected
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "publication decade")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[2]["display"], "the 1990's")
        self.assertIs(choices[2]["selected"], True)
        self.assertEqual(choices[2]["query_string"], "?decade__isnull=the+90s")