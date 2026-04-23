def test_render_delete_selected_confirmation_no_subtitle(self):
        post_data = {
            "action": "delete_selected",
            "selected_across": "0",
            "index": "0",
            "_selected_action": self.a1.pk,
        }
        with self.assertNoLogs("django.template", "DEBUG"):
            self.client.post(reverse("admin:admin_views_article_changelist"), post_data)