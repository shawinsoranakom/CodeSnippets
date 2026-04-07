def test_lookup_with_dynamic_value(self):
        """
        Ensure SimpleListFilter can access self.value() inside the lookup.
        """
        modeladmin = DepartmentFilterDynamicValueBookAdmin(Book, site)

        def _test_choices(request, expected_displays):
            request.user = self.alfred
            changelist = modeladmin.get_changelist_instance(request)
            filterspec = changelist.get_filters(request)[0][0]
            self.assertEqual(filterspec.title, "publication decade")
            choices = tuple(c["display"] for c in filterspec.choices(changelist))
            self.assertEqual(choices, expected_displays)

        _test_choices(
            self.request_factory.get("/", {}), ("All", "the 1980's", "the 1990's")
        )

        _test_choices(
            self.request_factory.get("/", {"publication-decade": "the 80s"}),
            ("All", "the 1990's"),
        )

        _test_choices(
            self.request_factory.get("/", {"publication-decade": "the 90s"}),
            ("All", "the 1980's"),
        )