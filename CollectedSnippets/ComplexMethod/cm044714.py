def test_custom_redirect_mixin(self, httpbin):
        """Tests a custom mixin to overwrite ``get_redirect_target``.

        Ensures a subclassed ``requests.Session`` can handle a certain type of
        malformed redirect responses.

        1. original request receives a proper response: 302 redirect
        2. following the redirect, a malformed response is given:
            status code = HTTP 200
            location = alternate url
        3. the custom session catches the edge case and follows the redirect
        """
        url_final = httpbin("html")
        querystring_malformed = urlencode({"location": url_final})
        url_redirect_malformed = httpbin("response-headers?%s" % querystring_malformed)
        querystring_redirect = urlencode({"url": url_redirect_malformed})
        url_redirect = httpbin("redirect-to?%s" % querystring_redirect)
        urls_test = [
            url_redirect,
            url_redirect_malformed,
            url_final,
        ]

        class CustomRedirectSession(requests.Session):
            def get_redirect_target(self, resp):
                # default behavior
                if resp.is_redirect:
                    return resp.headers["location"]
                # edge case - check to see if 'location' is in headers anyways
                location = resp.headers.get("location")
                if location and (location != resp.url):
                    return location
                return None

        session = CustomRedirectSession()
        r = session.get(urls_test[0])
        assert len(r.history) == 2
        assert r.status_code == 200
        assert r.history[0].status_code == 302
        assert r.history[0].is_redirect
        assert r.history[1].status_code == 200
        assert not r.history[1].is_redirect
        assert r.url == urls_test[2]