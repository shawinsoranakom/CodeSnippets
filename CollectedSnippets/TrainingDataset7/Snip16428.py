def test_post_save_message_no_forbidden_links_visible(self):
        """
        Post-save message shouldn't contain a link to the change form if the
        user doesn't have the change permission.
        """
        self.client.force_login(self.adduser)
        # Emulate Article creation for user with add-only permission.
        post_data = {
            "title": "Fun & games",
            "content": "Some content",
            "date_0": "2015-10-31",
            "date_1": "16:35:00",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_article_add"), post_data, follow=True
        )
        self.assertContains(
            response,
            '<li class="success">The article “Fun &amp; games” was added successfully.'
            "</li>",
            html=True,
        )