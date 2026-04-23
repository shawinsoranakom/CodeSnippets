def test_lookup_with_non_string_value_underscored(self):
        """
        Ensure SimpleListFilter lookups pass lookup_allowed checks when
        parameter_name attribute contains double-underscore value (#19182).
        """
        modeladmin = DepartmentFilterUnderscoredEmployeeAdmin(Employee, site)
        request = self.request_factory.get(
            "/", {"department__whatever": self.john.department.pk}
        )
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
            choices[1]["query_string"],
            "?department__whatever=%s" % self.john.department.pk,
        )