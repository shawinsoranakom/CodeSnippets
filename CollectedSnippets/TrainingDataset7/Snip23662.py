def test_parameter_substitution(self):
        "Redirection URLs can be parameterized"
        response = RedirectView.as_view(url="/bar/%(object_id)d/")(
            self.rf.get("/foo/42/"), object_id=42
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/bar/42/")