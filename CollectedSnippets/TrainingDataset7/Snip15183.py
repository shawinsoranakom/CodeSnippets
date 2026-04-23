def test_list_display_related_field_ordering(self):
        parent_a = Parent.objects.create(name="Alice")
        parent_z = Parent.objects.create(name="Zara")
        Child.objects.create(name="Alice's child", parent=parent_a)
        Child.objects.create(name="Zara's child", parent=parent_z)

        class ChildAdmin(admin.ModelAdmin):
            list_display = ["name", "parent__name"]
            list_per_page = 1

        m = ChildAdmin(Child, custom_site)

        # Order ascending.
        request = self._mocked_authenticated_request("/grandchild/?o=1", self.superuser)
        response = m.changelist_view(request)
        self.assertContains(response, parent_a.name)
        self.assertNotContains(response, parent_z.name)

        # Order descending.
        request = self._mocked_authenticated_request(
            "/grandchild/?o=-1", self.superuser
        )
        response = m.changelist_view(request)
        self.assertNotContains(response, parent_a.name)
        self.assertContains(response, parent_z.name)