def test_redirect(self):
        from_url = "http://example.com/a.html"
        to_url = "http://example.com/b.html"
        h = urllib.request.HTTPRedirectHandler()
        o = h.parent = MockOpener()

        # ordinary redirect behaviour
        for code in 301, 302, 303, 307, 308:
            for data in None, "blah\nblah\n":
                method = getattr(h, "http_error_%s" % code)
                req = Request(from_url, data)
                req.timeout = socket._GLOBAL_DEFAULT_TIMEOUT
                req.add_header("Nonsense", "viking=withhold")
                if data is not None:
                    req.add_header("Content-Length", str(len(data)))
                req.add_unredirected_header("Spam", "spam")
                try:
                    method(req, MockFile(), code, "Blah",
                           MockHeaders({"location": to_url}))
                except urllib.error.HTTPError as err:
                    # 307 and 308 in response to POST require user OK
                    self.assertIn(code, (307, 308))
                    self.assertIsNotNone(data)
                    err.close()
                self.assertEqual(o.req.get_full_url(), to_url)
                try:
                    self.assertEqual(o.req.get_method(), "GET")
                except AttributeError:
                    self.assertFalse(o.req.data)

                # now it's a GET, there should not be headers regarding content
                # (possibly dragged from before being a POST)
                headers = [x.lower() for x in o.req.headers]
                self.assertNotIn("content-length", headers)
                self.assertNotIn("content-type", headers)

                self.assertEqual(o.req.headers["Nonsense"],
                                 "viking=withhold")
                self.assertNotIn("Spam", o.req.headers)
                self.assertNotIn("Spam", o.req.unredirected_hdrs)

        # loop detection
        req = Request(from_url)
        req.timeout = socket._GLOBAL_DEFAULT_TIMEOUT

        def redirect(h, req, url=to_url):
            h.http_error_302(req, MockFile(), 302, "Blah",
                             MockHeaders({"location": url}))
        # Note that the *original* request shares the same record of
        # redirections with the sub-requests caused by the redirections.

        # detect infinite loop redirect of a URL to itself
        req = Request(from_url, origin_req_host="example.com")
        count = 0
        req.timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        try:
            while 1:
                redirect(h, req, "http://example.com/")
                count = count + 1
        except urllib.error.HTTPError as err:
            # don't stop until max_repeats, because cookies may introduce state
            self.assertEqual(count, urllib.request.HTTPRedirectHandler.max_repeats)
            err.close()

        # detect endless non-repeating chain of redirects
        req = Request(from_url, origin_req_host="example.com")
        count = 0
        req.timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        try:
            while 1:
                redirect(h, req, "http://example.com/%d" % count)
                count = count + 1
        except urllib.error.HTTPError as err:
            self.assertEqual(count,
                             urllib.request.HTTPRedirectHandler.max_redirections)
            err.close()