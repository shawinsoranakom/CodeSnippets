def test_no_list_display_links(self):
        """#15185 -- Allow no links from the 'change list' view grid."""
        p = Parent.objects.create(name="parent")
        m = NoListDisplayLinksParentAdmin(Parent, custom_site)
        superuser = self._create_superuser("superuser")
        request = self._mocked_authenticated_request("/parent/", superuser)
        response = m.changelist_view(request)
        link = reverse("admin:admin_changelist_parent_change", args=(p.pk,))
        self.assertNotContains(response, '<a href="%s">' % link)