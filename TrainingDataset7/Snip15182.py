def test_list_display_related_field_null(self):
        GrandChild.objects.create(name="I am parentless", parent=None)
        request = self._mocked_authenticated_request("/grandchild/", self.superuser)

        m = GrandChildAdmin(GrandChild, custom_site)
        response = m.changelist_view(request)
        self.assertContains(response, '<td class="field-parent__name">-</td>')
        self.assertContains(response, '<td class="field-parent__parent__name">-</td>')