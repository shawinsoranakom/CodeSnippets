def test_lookup_using_custom_divider(self):
        """
        Filter __in lookups with a custom divider.
        """
        jane = Employee.objects.create(name="Jane,Green", department=self.design)
        modeladmin = EmployeeCustomDividerFilterAdmin(Employee, site)
        employees = [jane, self.jack]

        request = self.request_factory.get(
            "/", {"name__in": "|".join(e.name for e in employees)}
        )
        # test for lookup with custom divider
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), employees)

        # test for lookup with comma in the lookup string
        request = self.request_factory.get("/", {"name": jane.name})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        # Make sure the correct queryset is returned
        queryset = changelist.get_queryset(request)
        self.assertEqual(list(queryset), [jane])