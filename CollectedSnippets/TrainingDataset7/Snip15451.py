def test_two_characters_long_field(self):
        """
        list_filter works with two-characters long field names (#16080).
        """
        modeladmin = BookAdmin(Book, site)
        request = self.request_factory.get("/", {"no": "207"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [self.bio_book])

        filterspec = changelist.get_filters(request)[0][5]
        self.assertEqual(filterspec.title, "number")
        choices = list(filterspec.choices(changelist))
        self.assertIs(choices[2]["selected"], True)
        self.assertEqual(choices[2]["query_string"], "?no=207")