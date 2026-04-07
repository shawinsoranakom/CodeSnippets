def test_change_view_with_view_only_inlines(self):
        """
        User with change permission to a section but view-only for inlines.
        """
        self.viewuser.user_permissions.add(
            get_perm(Section, get_permission_codename("change", Section._meta))
        )
        self.client.force_login(self.viewuser)
        # GET shows inlines.
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,))
        )
        self.assertEqual(len(response.context["inline_admin_formsets"]), 1)
        formset = response.context["inline_admin_formsets"][0]
        self.assertEqual(len(formset.forms), 3)
        # Valid POST changes the name.
        data = {
            "name": "Can edit name with view-only inlines",
            "article_set-TOTAL_FORMS": 3,
            "article_set-INITIAL_FORMS": 3,
        }
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), data
        )
        self.assertRedirects(response, reverse("admin:admin_views_section_changelist"))
        self.assertEqual(Section.objects.get(pk=self.s1.pk).name, data["name"])
        # Invalid POST reshows inlines.
        del data["name"]
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), data
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["inline_admin_formsets"]), 1)
        formset = response.context["inline_admin_formsets"][0]
        self.assertEqual(len(formset.forms), 3)