def test_include_args(self):
        "GET arguments can be included in the redirected URL"
        response = RedirectView.as_view(url="/bar/")(self.rf.get("/foo/"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/")

        response = RedirectView.as_view(url="/bar/", query_string=True)(
            self.rf.get("/foo/?pork=spam")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/?pork=spam")