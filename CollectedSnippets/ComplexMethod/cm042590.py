def test_system_proxy_proxied_https_to_unproxied_http(self):
            crawler = get_crawler()
            redirect_mw = self.mwcls.from_crawler(crawler)
            env = {
                "https_proxy": "https://b:@b.example",
            }
            with set_environ(**env):
                proxy_mw = HttpProxyMiddleware.from_crawler(crawler)

            request1 = Request("https://example.com")
            proxy_mw.process_request(request1)

            assert request1.headers["Proxy-Authorization"] == b"Basic Yjo="
            assert request1.meta["_auth_proxy"] == "https://b.example"
            assert request1.meta["proxy"] == "https://b.example"

            response1 = self.get_response(request1, "http://example.com")
            request2 = redirect_mw.process_response(request1, response1)

            assert isinstance(request2, Request)
            assert "Proxy-Authorization" not in request2.headers
            assert "_auth_proxy" not in request2.meta
            assert "proxy" not in request2.meta

            proxy_mw.process_request(request2)

            assert "Proxy-Authorization" not in request2.headers
            assert "_auth_proxy" not in request2.meta
            assert "proxy" not in request2.meta

            response2 = self.get_response(request2, "https://example.com")
            request3 = redirect_mw.process_response(request2, response2)

            assert isinstance(request3, Request)
            assert "Proxy-Authorization" not in request3.headers
            assert "_auth_proxy" not in request3.meta
            assert "proxy" not in request3.meta

            proxy_mw.process_request(request3)

            assert request3.headers["Proxy-Authorization"] == b"Basic Yjo="
            assert request3.meta["_auth_proxy"] == "https://b.example"
            assert request3.meta["proxy"] == "https://b.example"