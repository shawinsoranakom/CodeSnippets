def test_get_history_view(self):
        """
        Retrieving the history for an object using urlencoded form of primary
        key should work.
        Refs #12349, #18550.
        """
        response = self.client.get(
            reverse(
                "admin:admin_views_modelwithstringprimarykey_history", args=(self.pk,)
            )
        )
        self.assertContains(response, escape(self.pk))
        self.assertContains(response, "Changed something")