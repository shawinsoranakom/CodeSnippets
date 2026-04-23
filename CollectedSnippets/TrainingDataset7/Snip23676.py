def test_redirect_with_same_query_string_param_will_append_not_replace(self):
        response = RedirectView.as_view(url="/bar/?pork=spam", query_string=True)(
            self.rf.get("/foo/?utm_source=social&pork=ham")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["Location"], "/bar/?pork=spam&utm_source=social&pork=ham"
        )