def test_temporary_redirect(self):
        "Temporary redirects are an option"
        response = RedirectView.as_view(url="/bar/", permanent=False)(
            self.rf.get("/foo/")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/")