def test_redirect_response_status_code(self):
        tests = [
            (True, False, 301),
            (False, False, 302),
            (False, True, 307),
            (True, True, 308),
        ]
        for permanent, preserve_request, expected_status_code in tests:
            with self.subTest(permanent=permanent, preserve_request=preserve_request):
                response = redirect(
                    "/path/is/irrelevant/",
                    permanent=permanent,
                    preserve_request=preserve_request,
                )
                self.assertIsInstance(response, HttpResponseRedirectBase)
                self.assertEqual(response.status_code, expected_status_code)