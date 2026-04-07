def test_closes_connection_without_content_length(self):
        """
        An HTTP 1.1 server is supposed to support keep-alive. Since our
        development server is rather simple we support it only in cases where
        we can detect a content length from the response. This should be doable
        for all simple views and streaming responses where an iterable with
        length of one is passed. The latter follows as result of
        `set_content_length` from
        https://github.com/python/cpython/blob/main/Lib/wsgiref/handlers.py.

        If we cannot detect a content length we explicitly set the `Connection`
        header to `close` to notify the client that we do not actually support
        it.
        """
        conn = HTTPConnection(
            LiveServerViews.server_thread.host,
            LiveServerViews.server_thread.port,
            timeout=1,
        )
        self.addCleanup(conn.close)

        conn.request(
            "GET", "/streaming_example_view/", headers={"Connection": "keep-alive"}
        )
        response = conn.getresponse()
        self.assertTrue(response.will_close)
        self.assertEqual(response.read(), b"Iamastream")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Connection"), "close")

        conn.request("GET", "/streaming_example_view/", headers={"Connection": "close"})
        response = conn.getresponse()
        self.assertTrue(response.will_close)
        self.assertEqual(response.read(), b"Iamastream")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Connection"), "close")