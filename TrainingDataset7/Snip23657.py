def test_default_redirect(self):
        "Default is a temporary redirect"
        response = RedirectView.as_view(url="/bar/")(self.rf.get("/foo/"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/")