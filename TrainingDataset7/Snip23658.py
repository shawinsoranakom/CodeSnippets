def test_permanent_redirect(self):
        "Permanent redirects are an option"
        response = RedirectView.as_view(url="/bar/", permanent=True)(
            self.rf.get("/foo/")
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, "/bar/")