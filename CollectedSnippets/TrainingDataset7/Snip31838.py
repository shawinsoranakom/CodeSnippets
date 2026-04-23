def test_closes_connection_with_content_length(self):
        """
        Contrast to
        LiveServerViews.test_keep_alive_on_connection_with_content_length().
        Persistent connections require threading server.
        """
        conn = HTTPConnection(
            SingleThreadLiveServerViews.server_thread.host,
            SingleThreadLiveServerViews.server_thread.port,
            timeout=1,
        )
        self.addCleanup(conn.close)
        conn.request("GET", "/example_view/", headers={"Connection": "keep-alive"})
        response = conn.getresponse()
        self.assertTrue(response.will_close)
        self.assertEqual(response.read(), b"example view")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Connection"), "close")