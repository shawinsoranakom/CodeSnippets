def test_custom_model_admin_templates(self):
        # Test custom change list template with custom extra context
        response = self.client.get(
            reverse("admin:admin_views_customarticle_changelist")
        )
        self.assertContains(response, "var hello = 'Hello!';")
        self.assertTemplateUsed(response, "custom_admin/change_list.html")

        # Test custom add form template
        response = self.client.get(reverse("admin:admin_views_customarticle_add"))
        self.assertTemplateUsed(response, "custom_admin/add_form.html")

        # Add an article so we can test delete, change, and history views
        post = self.client.post(
            reverse("admin:admin_views_customarticle_add"),
            {
                "content": "<p>great article</p>",
                "date_0": "2008-03-18",
                "date_1": "10:54:39",
            },
        )
        self.assertRedirects(
            post, reverse("admin:admin_views_customarticle_changelist")
        )
        self.assertEqual(CustomArticle.objects.count(), 1)
        article_pk = CustomArticle.objects.all()[0].pk

        # Test custom delete, change, and object history templates
        # Test custom change form template
        response = self.client.get(
            reverse("admin:admin_views_customarticle_change", args=(article_pk,))
        )
        self.assertTemplateUsed(response, "custom_admin/change_form.html")
        response = self.client.get(
            reverse("admin:admin_views_customarticle_delete", args=(article_pk,))
        )
        self.assertTemplateUsed(response, "custom_admin/delete_confirmation.html")
        response = self.client.post(
            reverse("admin:admin_views_customarticle_changelist"),
            data={
                "index": 0,
                "action": ["delete_selected"],
                "_selected_action": ["1"],
            },
        )
        self.assertTemplateUsed(
            response, "custom_admin/delete_selected_confirmation.html"
        )
        response = self.client.get(
            reverse("admin:admin_views_customarticle_history", args=(article_pk,))
        )
        self.assertTemplateUsed(response, "custom_admin/object_history.html")

        # A custom popup response template may be specified by
        # ModelAdmin.popup_response_template.
        response = self.client.post(
            reverse("admin:admin_views_customarticle_add") + "?%s=1" % IS_POPUP_VAR,
            {
                "content": "<p>great article</p>",
                "date_0": "2008-03-18",
                "date_1": "10:54:39",
                IS_POPUP_VAR: "1",
            },
        )
        self.assertEqual(response.template_name, "custom_admin/popup_response.html")