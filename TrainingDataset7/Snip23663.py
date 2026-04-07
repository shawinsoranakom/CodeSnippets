def test_named_url_pattern(self):
        "Named pattern parameter should reverse to the matching pattern"
        response = RedirectView.as_view(pattern_name="artist_detail")(
            self.rf.get("/foo/"), pk=1
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/detail/artist/1/")