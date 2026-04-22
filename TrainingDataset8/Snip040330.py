def test_unix_socket(self):
        app = mock.MagicMock()

        config.set_option("server.address", "unix://~/fancy-test/testasd")
        some_socket = object()

        mock_server = self.get_httpserver()
        with patch(
            "streamlit.web.server.server.HTTPServer", return_value=mock_server
        ), patch.object(
            tornado.netutil, "bind_unix_socket", return_value=some_socket
        ) as bind_unix_socket, patch.dict(
            os.environ, {"HOME": "/home/superfakehomedir"}
        ):
            start_listening(app)

            bind_unix_socket.assert_called_with(
                "/home/superfakehomedir/fancy-test/testasd"
            )
            mock_server.add_socket.assert_called_with(some_socket)