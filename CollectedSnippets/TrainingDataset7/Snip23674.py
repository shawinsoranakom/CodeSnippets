def test_redirect_with_querry_string_in_destination(self):
        response = RedirectView.as_view(url="/bar/?pork=spam", query_string=True)(
            self.rf.get("/foo")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/bar/?pork=spam")