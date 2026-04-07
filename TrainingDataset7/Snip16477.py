def test_redirect_on_add_view_continue_button(self):
        """As soon as an object is added using "Save and continue editing"
        button, the user should be redirected to the object's change_view.

        In case primary key is a string containing some special characters
        like slash or underscore, these characters must be escaped (see #22266)
        """
        response = self.client.post(
            reverse("admin:admin_views_modelwithstringprimarykey_add"),
            {
                "string_pk": "123/history",
                "_continue": "1",  # Save and continue editing
            },
        )

        self.assertEqual(response.status_code, 302)  # temporary redirect
        self.assertIn("/123_2Fhistory/", response.headers["location"])