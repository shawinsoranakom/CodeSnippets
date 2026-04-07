def test_display_consecutive_whitespace_object_in_deleted_object(self):
        response = self.client.get(
            reverse("admin:admin_views_coverletter_delete", args=(self.obj.pk,))
        )
        self.assertContains(
            response,
            '<ul id="deleted-objects">'
            f'<li>Cover letter: <a href="{self.change_link}">-</a></li></ul>',
            html=True,
        )