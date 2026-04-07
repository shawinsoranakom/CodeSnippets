def test_list_display_related_field_boolean_display(self):
        """
        Related boolean fields (parent__is_active) display boolean icons.
        """
        parent = Parent.objects.create(name="Test Parent")
        child_active = Child.objects.create(
            name="Active Child", parent=parent, is_active=True
        )
        child_inactive = Child.objects.create(
            name="Inactive Child", parent=parent, is_active=False
        )

        class GrandChildAdmin(admin.ModelAdmin):
            list_display = ["name", "parent__is_active"]

        GrandChild.objects.create(name="GrandChild of Active", parent=child_active)
        GrandChild.objects.create(name="GrandChild of Inactive", parent=child_inactive)

        m = GrandChildAdmin(GrandChild, custom_site)
        request = self._mocked_authenticated_request("/grandchild/", self.superuser)
        response = m.changelist_view(request)

        # Boolean icons are rendered using img tags with specific alt text.
        self.assertContains(response, 'alt="True"')
        self.assertContains(response, 'alt="False"')
        # Ensure "True" and "False" text are NOT in the response.
        self.assertNotContains(response, ">True<")
        self.assertNotContains(response, ">False<")