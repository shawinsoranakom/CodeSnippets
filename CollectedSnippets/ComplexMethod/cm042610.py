def test_dont_merge_cookies(self):
        # merge some cookies into jar
        headers = {"Set-Cookie": "C1=value1; path=/"}
        req = Request("http://scrapytest.org/")
        res = Response("http://scrapytest.org/", headers=headers)
        assert self.mw.process_response(req, res) is res

        # test Cookie header is not seted to request
        req = Request("http://scrapytest.org/dontmerge", meta={"dont_merge_cookies": 1})
        assert self.mw.process_request(req) is None
        assert "Cookie" not in req.headers

        # check that returned cookies are not merged back to jar
        res = Response(
            "http://scrapytest.org/dontmerge",
            headers={"Set-Cookie": "dont=mergeme; path=/"},
        )
        assert self.mw.process_response(req, res) is res

        # check that cookies are merged back
        req = Request("http://scrapytest.org/mergeme")
        assert self.mw.process_request(req) is None
        assert req.headers.get("Cookie") == b"C1=value1"

        # check that cookies are merged when dont_merge_cookies is passed as 0
        req = Request("http://scrapytest.org/mergeme", meta={"dont_merge_cookies": 0})
        assert self.mw.process_request(req) is None
        assert req.headers.get("Cookie") == b"C1=value1"