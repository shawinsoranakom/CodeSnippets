def test_add_view_with_view_only_inlines(self, has_change_permission):
        """User with add permission to a section but view-only for inlines."""
        self.viewuser.user_permissions.add(
            get_perm(Section, get_permission_codename("add", Section._meta))
        )
        self.client.force_login(self.viewuser)
        # Valid POST creates a new section.
        data = {
            "name": "New obj",
            "article_set-TOTAL_FORMS": 0,
            "article_set-INITIAL_FORMS": 0,
        }
        response = self.client.post(reverse("admin:admin_views_section_add"), data)
        self.assertRedirects(response, reverse("admin:index"))
        self.assertEqual(Section.objects.latest("id").name, data["name"])
        # InlineModelAdmin.has_change_permission()'s obj argument is always
        # None during object add.
        self.assertEqual(
            [obj for (request, obj), _ in has_change_permission.call_args_list],
            [None, None],
        )