def test_list_display_related_field(self):
        parent = Parent.objects.create(name="I am your father")
        child = Child.objects.create(name="I am your child", parent=parent)
        GrandChild.objects.create(name="I am your grandchild", parent=child)
        request = self._mocked_authenticated_request("/grandchild/", self.superuser)

        m = GrandChildAdmin(GrandChild, custom_site)
        response = m.changelist_view(request)
        self.assertContains(response, parent.name)
        self.assertContains(response, child.name)