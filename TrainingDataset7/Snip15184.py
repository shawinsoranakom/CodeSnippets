def test_list_display_related_field_ordering_fields(self):
        class ChildAdmin(admin.ModelAdmin):
            list_display = ["name", "parent__name"]
            ordering = ["parent__name"]

        m = ChildAdmin(Child, custom_site)
        request = self._mocked_authenticated_request("/", self.superuser)
        cl = m.get_changelist_instance(request)
        self.assertEqual(cl.get_ordering_field_columns(), {2: "asc"})