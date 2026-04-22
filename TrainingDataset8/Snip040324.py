def test_rotates_a_hundred_ports(self):
        app = mock.MagicMock()

        RetriesExceeded = streamlit.web.server.server.RetriesExceeded
        with pytest.raises(RetriesExceeded) as pytest_wrapped_e:
            with patch(
                "streamlit.web.server.server.HTTPServer",
                return_value=self.get_httpserver(),
            ) as mock_server:
                start_listening(app)
                self.assertEqual(pytest_wrapped_e.type, SystemExit)
                self.assertEqual(pytest_wrapped_e.value.code, errno.EADDRINUSE)
                self.assertEqual(mock_server.listen.call_count, MAX_PORT_SEARCH_RETRIES)