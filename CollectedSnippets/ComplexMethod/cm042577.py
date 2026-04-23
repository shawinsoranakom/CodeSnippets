def test_meta_proxy_https_absolute(self):
            crawler = get_crawler()
            redirect_mw = self.mwcls.from_crawler(crawler)
            proxy_mw = HttpProxyMiddleware.from_crawler(crawler)

            meta = {"proxy": "https://a:@a.example"}
            request1 = Request("https://example.com", meta=meta)
            proxy_mw.process_request(request1)

            assert request1.headers["Proxy-Authorization"] == b"Basic YTo="
            assert request1.meta["_auth_proxy"] == "https://a.example"
            assert request1.meta["proxy"] == "https://a.example"

            response1 = self.get_response(request1, "https://example.com")
            request2 = redirect_mw.process_response(request1, response1)

            assert isinstance(request2, Request)
            assert request2.headers["Proxy-Authorization"] == b"Basic YTo="
            assert request2.meta["_auth_proxy"] == "https://a.example"
            assert request2.meta["proxy"] == "https://a.example"

            proxy_mw.process_request(request2)

            assert request2.headers["Proxy-Authorization"] == b"Basic YTo="
            assert request2.meta["_auth_proxy"] == "https://a.example"
            assert request2.meta["proxy"] == "https://a.example"

            response2 = self.get_response(request2, "https://example.com")
            request3 = redirect_mw.process_response(request2, response2)

            assert isinstance(request3, Request)
            assert request3.headers["Proxy-Authorization"] == b"Basic YTo="
            assert request3.meta["_auth_proxy"] == "https://a.example"
            assert request3.meta["proxy"] == "https://a.example"

            proxy_mw.process_request(request3)

            assert request3.headers["Proxy-Authorization"] == b"Basic YTo="
            assert request3.meta["_auth_proxy"] == "https://a.example"
            assert request3.meta["proxy"] == "https://a.example"