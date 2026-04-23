def test_redirect_to_querystring_only(self):
        """A URL that consists of a querystring only can be followed"""
        response = self.client.post("/post_then_get_view/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/post_then_get_view/")
        self.assertEqual(response.content, b"The value of success is true.")