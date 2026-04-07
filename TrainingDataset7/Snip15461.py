def test_emptylistfieldfilter_choices(self):
        modeladmin = BookAdminWithEmptyFieldListFilter(Book, site)
        request = self.request_factory.get("/")
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        filterspec = changelist.get_filters(request)[0][0]
        self.assertEqual(filterspec.title, "Verbose Author")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(len(choices), 3)

        self.assertEqual(choices[0]["display"], "All")
        self.assertIs(choices[0]["selected"], True)
        self.assertEqual(choices[0]["query_string"], "?")

        self.assertEqual(choices[1]["display"], "Empty")
        self.assertIs(choices[1]["selected"], False)
        self.assertEqual(choices[1]["query_string"], "?author__isempty=1")

        self.assertEqual(choices[2]["display"], "Not empty")
        self.assertIs(choices[2]["selected"], False)
        self.assertEqual(choices[2]["query_string"], "?author__isempty=0")