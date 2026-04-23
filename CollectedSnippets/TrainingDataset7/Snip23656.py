def test_no_url(self):
        "Without any configuration, returns HTTP 410 GONE"
        response = RedirectView.as_view()(self.rf.get("/foo/"))
        self.assertEqual(response.status_code, 410)