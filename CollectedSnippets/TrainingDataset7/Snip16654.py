def test_tags(self):
        response = self.client.get(reverse("django-admindocs-tags"))

        # The builtin tag group exists
        self.assertContains(response, "<h2>Built-in tags</h2>", count=2, html=True)

        # A builtin tag exists in both the index and detail
        self.assertContains(
            response, '<h3 id="built_in-autoescape">autoescape</h3>', html=True
        )
        self.assertContains(
            response,
            '<li><a href="#built_in-autoescape">autoescape</a></li>',
            html=True,
        )

        # An app tag exists in both the index and detail
        self.assertContains(
            response, '<h3 id="flatpages-get_flatpages">get_flatpages</h3>', html=True
        )
        self.assertContains(
            response,
            '<li><a href="#flatpages-get_flatpages">get_flatpages</a></li>',
            html=True,
        )

        # The admin list tag group exists
        self.assertContains(response, "<h2>admin_list</h2>", count=2, html=True)

        # An admin list tag exists in both the index and detail
        self.assertContains(
            response, '<h3 id="admin_list-admin_actions">admin_actions</h3>', html=True
        )
        self.assertContains(
            response,
            '<li><a href="#admin_list-admin_actions">admin_actions</a></li>',
            html=True,
        )