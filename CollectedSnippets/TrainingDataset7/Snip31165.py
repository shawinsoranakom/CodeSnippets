def test_create_cookie_after_deleting_cookie(self):
        """Setting a cookie after deletion clears the expiry date."""
        response = HttpResponse()
        response.set_cookie("c", "old-value")
        self.assertEqual(response.cookies["c"]["expires"], "")
        response.delete_cookie("c")
        self.assertEqual(
            response.cookies["c"]["expires"], "Thu, 01 Jan 1970 00:00:00 GMT"
        )
        response.set_cookie("c", "new-value")
        self.assertEqual(response.cookies["c"]["expires"], "")