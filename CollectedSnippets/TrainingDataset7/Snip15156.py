def test_dynamic_list_display(self):
        """
        Regression tests for #14206: dynamic list_display support.
        """
        parent = Parent.objects.create(name="parent")
        for i in range(10):
            Child.objects.create(name="child %s" % i, parent=parent)

        user_noparents = self._create_superuser("noparents")
        user_parents = self._create_superuser("parents")

        # Test with user 'noparents'
        m = custom_site.get_model_admin(Child)
        request = self._mocked_authenticated_request("/child/", user_noparents)
        response = m.changelist_view(request)
        self.assertNotContains(response, "Parent object")

        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        self.assertEqual(list_display, ["name", "age"])
        self.assertEqual(list_display_links, ["name"])

        # Test with user 'parents'
        m = DynamicListDisplayChildAdmin(Child, custom_site)
        request = self._mocked_authenticated_request("/child/", user_parents)
        response = m.changelist_view(request)
        self.assertContains(response, "Parent object")

        custom_site.unregister(Child)

        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        self.assertEqual(list_display, ("parent", "name", "age"))
        self.assertEqual(list_display_links, ["parent"])

        # Test default implementation
        custom_site.register(Child, ChildAdmin)
        m = custom_site.get_model_admin(Child)
        request = self._mocked_authenticated_request("/child/", user_noparents)
        response = m.changelist_view(request)
        self.assertContains(response, "Parent object")