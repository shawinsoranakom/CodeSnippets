def test_change_view_with_view_and_add_inlines(self):
        """User has view and add permissions on the inline model."""
        self.viewuser.user_permissions.add(
            get_perm(Section, get_permission_codename("change", Section._meta))
        )
        self.viewuser.user_permissions.add(
            get_perm(Article, get_permission_codename("add", Article._meta))
        )
        self.client.force_login(self.viewuser)
        # GET shows inlines.
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,))
        )
        self.assertEqual(len(response.context["inline_admin_formsets"]), 1)
        formset = response.context["inline_admin_formsets"][0]
        self.assertEqual(len(formset.forms), 6)
        # Valid POST creates a new article.
        data = {
            "name": "Can edit name with view-only inlines",
            "article_set-TOTAL_FORMS": 6,
            "article_set-INITIAL_FORMS": 3,
            "article_set-3-id": [""],
            "article_set-3-title": ["A title"],
            "article_set-3-content": ["Added content"],
            "article_set-3-date_0": ["2008-3-18"],
            "article_set-3-date_1": ["11:54:58"],
            "article_set-3-section": [str(self.s1.pk)],
        }
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), data
        )
        self.assertRedirects(response, reverse("admin:admin_views_section_changelist"))
        self.assertEqual(Section.objects.get(pk=self.s1.pk).name, data["name"])
        self.assertEqual(Article.objects.count(), 4)
        # Invalid POST reshows inlines.
        del data["name"]
        response = self.client.post(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,)), data
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["inline_admin_formsets"]), 1)
        formset = response.context["inline_admin_formsets"][0]
        self.assertEqual(len(formset.forms), 6)