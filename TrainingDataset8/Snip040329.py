def get_httpserver():
        httpserver = mock.MagicMock()

        httpserver.add_socket = mock.Mock()

        return httpserver