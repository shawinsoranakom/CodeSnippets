def test_bom_is_removed_from_body(self):
        # Inferring encoding from body also cache decoded body as sideeffect,
        # this test tries to ensure that calling response.encoding and
        # response.text in indistinct order doesn't affect final
        # response.text in indistinct order doesn't affect final
        # values for encoding and decoded body.
        url = "http://example.com"
        body = b"\xef\xbb\xbfWORD"
        headers = {"Content-type": ["text/html; charset=utf-8"]}

        # Test response without content-type and BOM encoding
        response = self.response_class(url, body=body)
        assert response.encoding == "utf-8"
        assert response.text == "WORD"
        response = self.response_class(url, body=body)
        assert response.text == "WORD"
        assert response.encoding == "utf-8"

        # Body caching sideeffect isn't triggered when encoding is declared in
        # content-type header but BOM still need to be removed from decoded
        # body
        response = self.response_class(url, headers=headers, body=body)
        assert response.encoding == "utf-8"
        assert response.text == "WORD"
        response = self.response_class(url, headers=headers, body=body)
        assert response.text == "WORD"
        assert response.encoding == "utf-8"