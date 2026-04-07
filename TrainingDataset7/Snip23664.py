def test_named_url_pattern_using_args(self):
        response = RedirectView.as_view(pattern_name="artist_detail")(
            self.rf.get("/foo/"), 1
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/detail/artist/1/")