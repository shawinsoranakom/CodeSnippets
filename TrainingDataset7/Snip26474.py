def test_cookie_settings(self):
        """
        CookieStorage honors SESSION_COOKIE_DOMAIN, SESSION_COOKIE_SECURE, and
        SESSION_COOKIE_HTTPONLY (#15618, #20972).
        """
        # Test before the messages have been consumed
        storage = self.get_storage()
        response = self.get_response()
        storage.add(constants.INFO, "test")
        storage.update(response)
        messages = storage._decode(response.cookies["messages"].value)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, "test")
        self.assertEqual(response.cookies["messages"]["domain"], ".example.com")
        self.assertEqual(response.cookies["messages"]["expires"], "")
        self.assertIs(response.cookies["messages"]["secure"], True)
        self.assertIs(response.cookies["messages"]["httponly"], True)
        self.assertEqual(response.cookies["messages"]["samesite"], "Strict")

        # Deletion of the cookie (storing with an empty value) after the
        # messages have been consumed.
        storage = self.get_storage()
        response = self.get_response()
        storage.add(constants.INFO, "test")
        for m in storage:
            pass  # Iterate through the storage to simulate consumption of messages.
        storage.update(response)
        self.assertEqual(response.cookies["messages"].value, "")
        self.assertEqual(response.cookies["messages"]["domain"], ".example.com")
        self.assertEqual(
            response.cookies["messages"]["expires"], "Thu, 01 Jan 1970 00:00:00 GMT"
        )
        self.assertEqual(
            response.cookies["messages"]["samesite"],
            settings.SESSION_COOKIE_SAMESITE,
        )