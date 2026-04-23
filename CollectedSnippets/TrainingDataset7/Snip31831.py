def test_keep_alive_connection_clears_previous_request_data(self):
        conn = HTTPConnection(
            LiveServerViews.server_thread.host, LiveServerViews.server_thread.port
        )
        self.addCleanup(conn.close)

        conn.request(
            "POST", "/method_view/", b"{}", headers={"Connection": "keep-alive"}
        )
        response = conn.getresponse()
        self.assertFalse(response.will_close)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), b"POST")

        conn.request("POST", "/method_view/", b"{}", headers={"Connection": "close"})
        response = conn.getresponse()
        self.assertFalse(response.will_close)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), b"POST")