def test_redirect_with_query_string_in_destination_and_request(self):
        response = RedirectView.as_view(url="/bar/?pork=spam", query_string=True)(
            self.rf.get("/foo/?utm_source=social")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["Location"], "/bar/?pork=spam&utm_source=social"
        )