def test_change_view_with_view_only_last_inline(self):
        self.viewuser.user_permissions.add(
            get_perm(Section, get_permission_codename("view", Section._meta))
        )
        self.client.force_login(self.viewuser)
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,))
        )
        self.assertEqual(len(response.context["inline_admin_formsets"]), 1)
        formset = response.context["inline_admin_formsets"][0]
        self.assertEqual(len(formset.forms), 3)
        # The last inline is not marked as empty.
        self.assertContains(response, 'id="article_set-2"')