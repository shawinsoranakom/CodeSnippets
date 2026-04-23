def test_get_change_view(self):
        """
        Retrieving the object using urlencoded form of primary key should work
        """
        response = self.client.get(
            reverse(
                "admin:admin_views_modelwithstringprimarykey_change", args=(self.pk,)
            )
        )
        self.assertContains(response, escape(self.pk))