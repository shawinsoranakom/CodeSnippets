def get_httpserver():
        httpserver = mock.MagicMock()

        httpserver.listen = mock.Mock()
        httpserver.listen.side_effect = OSError(errno.EADDRINUSE, "test", "asd")

        return httpserver