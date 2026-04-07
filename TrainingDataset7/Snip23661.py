def test_include_urlencoded_args(self):
        "GET arguments can be URL-encoded when included in the redirected URL"
        response = RedirectView.as_view(url="/bar/", query_string=True)(
            self.rf.get("/foo/?unicode=%E2%9C%93")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/?unicode=%E2%9C%93")