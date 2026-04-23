def test_admin_URLs_no_clash(self):
        # Should get the change_view for model instance with PK 'add', not show
        # the add_view
        url = reverse(
            "admin_custom_urls:%s_action_change" % Action._meta.app_label,
            args=(quote("add"),),
        )
        response = self.client.get(url)
        self.assertContains(response, "Change action")

        # Should correctly get the change_view for the model instance with the
        # funny-looking PK (the one with a 'path/to/html/document.html' value)
        url = reverse(
            "admin_custom_urls:%s_action_change" % Action._meta.app_label,
            args=(quote("path/to/html/document.html"),),
        )
        response = self.client.get(url)
        self.assertContains(response, "Change action")
        self.assertContains(response, 'value="path/to/html/document.html"')