def test_redirect_PATCH(self):
        "Default is a temporary redirect"
        response = RedirectView.as_view(url="/bar/")(self.rf.patch("/foo/"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/")