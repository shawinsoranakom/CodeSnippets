def test_system_proxy_unproxied_http_to_unproxied_https(self):
            crawler = get_crawler()
            redirect_mw = self.mwcls.from_crawler(crawler)
            proxy_mw = HttpProxyMiddleware.from_crawler(crawler)

            request1 = Request("http://example.com")
            proxy_mw.process_request(request1)

            assert "Proxy-Authorization" not in request1.headers
            assert "_auth_proxy" not in request1.meta
            assert "proxy" not in request1.meta

            response1 = self.get_response(request1, "https://example.com")
            request2 = redirect_mw.process_response(request1, response1)

            assert isinstance(request2, Request)
            assert "Proxy-Authorization" not in request2.headers
            assert "_auth_proxy" not in request2.meta
            assert "proxy" not in request2.meta

            proxy_mw.process_request(request2)

            assert "Proxy-Authorization" not in request2.headers
            assert "_auth_proxy" not in request2.meta
            assert "proxy" not in request2.meta

            response2 = self.get_response(request2, "http://example.com")
            request3 = redirect_mw.process_response(request2, response2)

            assert isinstance(request3, Request)
            assert "Proxy-Authorization" not in request3.headers
            assert "_auth_proxy" not in request3.meta
            assert "proxy" not in request3.meta

            proxy_mw.process_request(request3)

            assert "Proxy-Authorization" not in request3.headers
            assert "_auth_proxy" not in request3.meta
            assert "proxy" not in request3.meta