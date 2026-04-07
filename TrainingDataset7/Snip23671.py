def test_redirect_when_meta_contains_no_query_string(self):
        "regression for #16705"
        # we can't use self.rf.get because it always sets QUERY_STRING
        response = RedirectView.as_view(url="/bar/")(self.rf.request(PATH_INFO="/foo/"))
        self.assertEqual(response.status_code, 302)