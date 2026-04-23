def test_file_wrapper(self):
        """
        FileResponse uses wsgi.file_wrapper.
        """

        class FileWrapper:
            def __init__(self, filelike, block_size=None):
                self.block_size = block_size
                filelike.close()

        application = get_wsgi_application()
        environ = self.request_factory._base_environ(
            PATH_INFO="/file/",
            REQUEST_METHOD="GET",
            **{"wsgi.file_wrapper": FileWrapper},
        )
        response_data = {}

        def start_response(status, headers):
            response_data["status"] = status
            response_data["headers"] = headers

        response = application(environ, start_response)
        self.assertEqual(response_data["status"], "200 OK")
        self.assertIsInstance(response, FileWrapper)
        self.assertEqual(response.block_size, FileResponse.block_size)