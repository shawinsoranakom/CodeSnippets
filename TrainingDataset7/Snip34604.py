def test_follow_307_and_308_preserves_get_params(self):
        data = {"var": 30, "to": "/get_view/"}
        for code in (307, 308):
            with self.subTest(code=code):
                response = self.client.get(
                    "/redirect_view_%s/" % code, data=data, follow=True
                )
                self.assertContains(response, "30 is the value")