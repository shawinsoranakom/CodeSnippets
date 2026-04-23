def test_change_view_with_view_and_delete_inlines(self):
        """User has view and delete permissions on the inline model."""
        self.viewuser.user_permissions.add(
            get_perm(Section, get_permission_codename("change", Section._meta))
        )
        self.client.force_login(self.viewuser)
        data = {
            "name": "Name is required.",
            "article_set-TOTAL_FORMS": 6,
            "article_set-INITIAL_FORMS": 3,
            "article_set-0-id": [str(self.a1.pk)],
            "article_set-0-DELETE": ["on"],
        }
        # Inline POST details are ignored without delete permission.
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), data
        )
        self.assertRedirects(response, reverse("admin:admin_views_section_changelist"))
        self.assertEqual(Article.objects.count(), 3)
        # Deletion successful when delete permission is added.
        self.viewuser.user_permissions.add(
            get_perm(Article, get_permission_codename("delete", Article._meta))
        )
        data = {
            "name": "Name is required.",
            "article_set-TOTAL_FORMS": 6,
            "article_set-INITIAL_FORMS": 3,
            "article_set-0-id": [str(self.a1.pk)],
            "article_set-0-DELETE": ["on"],
        }
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), data
        )
        self.assertRedirects(response, reverse("admin:admin_views_section_changelist"))
        self.assertEqual(Article.objects.count(), 2)