def test_dynamic_list_filter(self):
        """
        Regression tests for ticket #17646: dynamic list_filter support.
        """
        parent = Parent.objects.create(name="parent")
        for i in range(10):
            Child.objects.create(name="child %s" % i, parent=parent)

        user_noparents = self._create_superuser("noparents")
        user_parents = self._create_superuser("parents")

        # Test with user 'noparents'
        m = DynamicListFilterChildAdmin(Child, custom_site)
        request = self._mocked_authenticated_request("/child/", user_noparents)
        response = m.changelist_view(request)
        self.assertEqual(response.context_data["cl"].list_filter, ["name", "age"])

        # Test with user 'parents'
        m = DynamicListFilterChildAdmin(Child, custom_site)
        request = self._mocked_authenticated_request("/child/", user_parents)
        response = m.changelist_view(request)
        self.assertEqual(
            response.context_data["cl"].list_filter, ("parent", "name", "age")
        )