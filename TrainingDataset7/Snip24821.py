def test_redirect_modifiers(self):
        cases = [
            (HttpResponseRedirect, "Moved temporarily", False, 302),
            (HttpResponseRedirect, "Moved temporarily preserve method", True, 307),
            (HttpResponsePermanentRedirect, "Moved permanently", False, 301),
            (
                HttpResponsePermanentRedirect,
                "Moved permanently preserve method",
                True,
                308,
            ),
        ]
        for response_class, content, preserve_request, expected_status_code in cases:
            with self.subTest(status_code=expected_status_code):
                response = response_class(
                    "/redirected/", content=content, preserve_request=preserve_request
                )
                self.assertEqual(response.status_code, expected_status_code)
                self.assertEqual(response.content.decode(), content)
                self.assertEqual(response.url, response.headers["Location"])