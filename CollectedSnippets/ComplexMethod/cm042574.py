def test_cross_origin_header_dropping(self):
            safe_headers = {"A": "B"}
            cookie_header = {"Cookie": "a=b"}
            authorization_header = {"Authorization": "Bearer 123456"}

            original_request = Request(
                "https://example.com",
                headers={**safe_headers, **cookie_header, **authorization_header},
            )

            # Redirects to the same origin (same scheme, same domain, same port)
            # keep all headers.
            internal_response = self.get_response(
                original_request, "https://example.com/a"
            )
            internal_redirect_request = self.mw.process_response(
                original_request, internal_response
            )
            assert isinstance(internal_redirect_request, Request)
            assert original_request.headers == internal_redirect_request.headers

            # Redirects to the same origin (same scheme, same domain, same port)
            # keep all headers also when the scheme is http.
            http_request = Request(
                "http://example.com",
                headers={**safe_headers, **cookie_header, **authorization_header},
            )
            http_response = self.get_response(http_request, "http://example.com/a")
            http_redirect_request = self.mw.process_response(
                http_request, http_response
            )
            assert isinstance(http_redirect_request, Request)
            assert http_request.headers == http_redirect_request.headers

            # For default ports, whether the port is explicit or implicit does not
            # affect the outcome, it is still the same origin.
            to_explicit_port_response = self.get_response(
                original_request, "https://example.com:443/a"
            )
            to_explicit_port_redirect_request = self.mw.process_response(
                original_request, to_explicit_port_response
            )
            assert isinstance(to_explicit_port_redirect_request, Request)
            assert original_request.headers == to_explicit_port_redirect_request.headers

            # For default ports, whether the port is explicit or implicit does not
            # affect the outcome, it is still the same origin.
            to_implicit_port_response = self.get_response(
                original_request, "https://example.com/a"
            )
            to_implicit_port_redirect_request = self.mw.process_response(
                original_request, to_implicit_port_response
            )
            assert isinstance(to_implicit_port_redirect_request, Request)
            assert original_request.headers == to_implicit_port_redirect_request.headers

            # A port change drops the Authorization header because the origin
            # changes, but keeps the Cookie header because the domain remains the
            # same.
            different_port_response = self.get_response(
                original_request, "https://example.com:8080/a"
            )
            different_port_redirect_request = self.mw.process_response(
                original_request, different_port_response
            )
            assert isinstance(different_port_redirect_request, Request)
            assert {
                **safe_headers,
                **cookie_header,
            } == different_port_redirect_request.headers.to_unicode_dict()

            # A domain change drops both the Authorization and the Cookie header.
            external_response = self.get_response(
                original_request, "https://example.org/a"
            )
            external_redirect_request = self.mw.process_response(
                original_request, external_response
            )
            assert isinstance(external_redirect_request, Request)
            assert safe_headers == external_redirect_request.headers.to_unicode_dict()

            # A scheme upgrade (http → https) drops the Authorization header
            # because the origin changes, but keeps the Cookie header because the
            # domain remains the same.
            upgrade_response = self.get_response(http_request, "https://example.com/a")
            upgrade_redirect_request = self.mw.process_response(
                http_request, upgrade_response
            )
            assert isinstance(upgrade_redirect_request, Request)
            assert {
                **safe_headers,
                **cookie_header,
            } == upgrade_redirect_request.headers.to_unicode_dict()

            # A scheme downgrade (https → http) drops the Authorization header
            # because the origin changes, and the Cookie header because its value
            # cannot indicate whether the cookies were secure (HTTPS-only) or not.
            #
            # Note: If the Cookie header is set by the cookie management
            # middleware, as recommended in the docs, the dropping of Cookie on
            # scheme downgrade is not an issue, because the cookie management
            # middleware will add again the Cookie header to the new request if
            # appropriate.
            downgrade_response = self.get_response(
                original_request, "http://example.com/a"
            )
            downgrade_redirect_request = self.mw.process_response(
                original_request, downgrade_response
            )
            assert isinstance(downgrade_redirect_request, Request)
            assert safe_headers == downgrade_redirect_request.headers.to_unicode_dict()