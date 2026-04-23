def test_change_view_without_preserved_filters(self):
        response = self.client.get(self.get_change_url(add_preserved_filters=False))
        # The action attribute is omitted.
        self.assertContains(response, '<form method="post" id="user_form" novalidate>')