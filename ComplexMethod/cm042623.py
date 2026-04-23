def test_process_response_zstd(self):
        _skip_if_no_zstd()

        raw_content = None
        for check_key in FORMAT:
            if not check_key.startswith("zstd-"):
                continue
            response = self._getresponse(check_key)
            request = response.request
            assert response.headers["Content-Encoding"] == b"zstd"
            newresponse = self.mw.process_response(request, response)
            if raw_content is None:
                raw_content = newresponse.body
            else:
                assert raw_content == newresponse.body
            assert newresponse is not response
            assert newresponse.body.startswith(b"<!DOCTYPE")
            assert "Content-Encoding" not in newresponse.headers