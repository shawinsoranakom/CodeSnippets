def test_dynamic_list_display_links(self):
        """
        Regression tests for #16257: dynamic list_display_links support.
        """
        parent = Parent.objects.create(name="parent")
        for i in range(1, 10):
            Child.objects.create(id=i, name="child %s" % i, parent=parent, age=i)

        m = DynamicListDisplayLinksChildAdmin(Child, custom_site)
        superuser = self._create_superuser("superuser")
        request = self._mocked_authenticated_request("/child/", superuser)
        response = m.changelist_view(request)
        for i in range(1, 10):
            link = reverse("admin:admin_changelist_child_change", args=(i,))
            self.assertContains(response, '<a href="%s">%s</a>' % (link, i))

        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        self.assertEqual(list_display, ("parent", "name", "age"))
        self.assertEqual(list_display_links, ["age"])