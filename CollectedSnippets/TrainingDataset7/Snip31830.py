def test_keep_alive_on_connection_with_content_length(self):
        """
        See `test_closes_connection_without_content_length` for details. This
        is a follow up test, which ensure that we do not close the connection
        if not needed, hence allowing us to take advantage of keep-alive.
        """
        conn = HTTPConnection(
            LiveServerViews.server_thread.host, LiveServerViews.server_thread.port
        )
        self.addCleanup(conn.close)

        conn.request("GET", "/example_view/", headers={"Connection": "keep-alive"})
        response = conn.getresponse()
        self.assertFalse(response.will_close)
        self.assertEqual(response.read(), b"example view")
        self.assertEqual(response.status, 200)
        self.assertIsNone(response.getheader("Connection"))

        conn.request("GET", "/example_view/", headers={"Connection": "close"})
        response = conn.getresponse()
        self.assertFalse(response.will_close)
        self.assertEqual(response.read(), b"example view")
        self.assertEqual(response.status, 200)
        self.assertIsNone(response.getheader("Connection"))