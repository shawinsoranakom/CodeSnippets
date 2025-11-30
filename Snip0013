def test_has_cloudflare_protection_with_code_403_and_503_in_response(self):
        resp_with_cloudflare_protection_code_403 = FakeResponse(
            code=self.code_403,
            headers=self.cloudflare_headers,
            text=self.text_with_cloudflare_flags
        )

        resp_with_cloudflare_protection_code_503 = FakeResponse(
            code=self.code_503,
            headers=self.cloudflare_headers,
            text=self.text_with_cloudflare_flags
        )

        result1 = has_cloudflare_protection(resp_with_cloudflare_protection_code_403)
        result2 = has_cloudflare_protection(resp_with_cloudflare_protection_code_503)

        self.assertTrue(result1)
        self.assertTrue(result2)

    def test_has_cloudflare_protection_when_there_is_no_protection(self):
        resp_without_cloudflare_protection1 = FakeResponse(
            code=self.code_200,
            headers=self.no_cloudflare_headers,
            text=self.text_without_cloudflare_flags
        )

        resp_without_cloudflare_protection2 = FakeResponse(
            code=self.code_403,
            headers=self.no_cloudflare_headers,
            text=self.text_without_cloudflare_flags
        )

        resp_without_cloudflare_protection3 = FakeResponse(
            code=self.code_503,
            headers=self.no_cloudflare_headers,
            text=self.text_without_cloudflare_flags
        )

        result1 = has_cloudflare_protection(resp_without_cloudflare_protection1)
        result2 = has_cloudflare_protection(resp_without_cloudflare_protection2)
        result3 = has_cloudflare_protection(resp_without_cloudflare_protection3)

        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)
