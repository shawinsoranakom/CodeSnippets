def test_cookiejar_key(self):
        req = Request(
            "http://scrapytest.org/",
            cookies={"galleta": "salada"},
            meta={"cookiejar": "store1"},
        )
        assert self.mw.process_request(req) is None
        assert req.headers.get("Cookie") == b"galleta=salada"

        headers = {"Set-Cookie": "C1=value1; path=/"}
        res = Response("http://scrapytest.org/", headers=headers, request=req)
        assert self.mw.process_response(req, res) is res

        req2 = Request("http://scrapytest.org/", meta=res.meta)
        assert self.mw.process_request(req2) is None
        self.assertCookieValEqual(
            req2.headers.get("Cookie"), b"C1=value1; galleta=salada"
        )

        req3 = Request(
            "http://scrapytest.org/",
            cookies={"galleta": "dulce"},
            meta={"cookiejar": "store2"},
        )
        assert self.mw.process_request(req3) is None
        assert req3.headers.get("Cookie") == b"galleta=dulce"

        headers = {"Set-Cookie": "C2=value2; path=/"}
        res2 = Response("http://scrapytest.org/", headers=headers, request=req3)
        assert self.mw.process_response(req3, res2) is res2

        req4 = Request("http://scrapytest.org/", meta=res2.meta)
        assert self.mw.process_request(req4) is None
        self.assertCookieValEqual(
            req4.headers.get("Cookie"), b"C2=value2; galleta=dulce"
        )

        # cookies from hosts with port
        req5_1 = Request("http://scrapytest.org:1104/")
        assert self.mw.process_request(req5_1) is None

        headers = {"Set-Cookie": "C1=value1; path=/"}
        res5_1 = Response(
            "http://scrapytest.org:1104/", headers=headers, request=req5_1
        )
        assert self.mw.process_response(req5_1, res5_1) is res5_1

        req5_2 = Request("http://scrapytest.org:1104/some-redirected-path")
        assert self.mw.process_request(req5_2) is None
        assert req5_2.headers.get("Cookie") == b"C1=value1"

        req5_3 = Request("http://scrapytest.org/some-redirected-path")
        assert self.mw.process_request(req5_3) is None
        assert req5_3.headers.get("Cookie") == b"C1=value1"

        # skip cookie retrieval for not http request
        req6 = Request("file:///scrapy/sometempfile")
        assert self.mw.process_request(req6) is None
        assert req6.headers.get("Cookie") is None