def test_link_field_display_links(self):
        self.client.force_login(self.superuser)
        g = Genre.objects.create(
            name="Blues",
            file="documents/blues_history.txt",
            url="http://blues_history.com",
        )
        response = self.client.get(reverse("admin:admin_changelist_genre_changelist"))
        self.assertContains(
            response,
            '<a href="/admin/admin_changelist/genre/%s/change/">'
            "documents/blues_history.txt</a>" % g.pk,
        )
        self.assertContains(
            response,
            '<a href="/admin/admin_changelist/genre/%s/change/">'
            "http://blues_history.com</a>" % g.pk,
        )