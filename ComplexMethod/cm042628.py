def test_redirect_strips_content_headers(self):
        url = "http://www.example.com/303"
        url2 = "http://www.example.com/redirected"
        headers = {
            "Content-Type": "application/json",
            "Content-Length": "100",
            "Content-Encoding": "gzip",
            "Content-Language": "en",
            "Content-Location": "http://www.example.com/original",
            "X-Custom": "foo",
        }
        req = Request(url, method="POST", headers=headers, body=b"foo")
        rsp = Response(url, headers={"Location": url2}, status=303)

        req2 = self.mw.process_response(req, rsp)
        assert isinstance(req2, Request)
        assert req2.url == url2
        assert req2.method == "GET"
        assert req2.body == b""
        assert "Content-Type" not in req2.headers
        assert "Content-Length" not in req2.headers
        assert "Content-Encoding" not in req2.headers
        assert "Content-Language" not in req2.headers
        assert "Content-Location" not in req2.headers
        assert req2.headers["X-Custom"] == b"foo"