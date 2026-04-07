def test_redirect_HEAD(self):
        "Default is a temporary redirect"
        response = RedirectView.as_view(url="/bar/")(self.rf.head("/foo/"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/")