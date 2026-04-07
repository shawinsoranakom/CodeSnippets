def test_follow_307_and_308_preserves_post_data(self):
        for code in (307, 308):
            with self.subTest(code=code):
                response = self.client.post(
                    "/redirect_view_%s/" % code, data={"value": "test"}, follow=True
                )
                self.assertContains(response, "test is the value")