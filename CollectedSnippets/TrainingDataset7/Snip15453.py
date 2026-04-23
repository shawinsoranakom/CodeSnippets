def test_lookup_with_non_string_value(self):
        """
        Ensure choices are set the selected class when using non-string values
        for lookups in SimpleListFilters (#19318).
        """
        modeladmin = DepartmentFilterEmployeeAdmin(Employee, site)
        request = self.request_factory.get("/", {"department": self.john.department.pk})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)

        queryset = changelist.get_queryset(request)

        self.assertEqual(list(queryset), [self.john])

        filterspec = changelist.get_filters(request)[0][-1]
        self.assertEqual(filterspec.title, "department")
        choices = list(filterspec.choices(changelist))
        self.assertEqual(choices[1]["display"], "DEV")
        self.assertIs(choices[1]["selected"], True)
        self.assertEqual(
            choices[1]["query_string"], "?department=%s" % self.john.department.pk
        )