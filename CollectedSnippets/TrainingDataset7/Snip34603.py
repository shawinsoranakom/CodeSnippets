def test_follow_307_and_308_preserves_put_body(self):
        for code in (307, 308):
            with self.subTest(code=code):
                response = self.client.put(
                    "/redirect_view_%s/?to=/put_view/" % code, data="a=b", follow=True
                )
                self.assertContains(response, "a=b is the body")