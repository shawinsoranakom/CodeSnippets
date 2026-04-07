async def test_file_response(self):
        """
        Makes sure that FileResponse works over ASGI.
        """
        application = get_asgi_application()
        # Construct HTTP request.
        scope = self.async_request_factory._base_scope(path="/file/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        # Get the file content.
        with open(test_filename, "rb") as test_file:
            test_file_contents = test_file.read()
        # Read the response.
        with captured_stderr():
            response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        headers = response_start["headers"]
        self.assertEqual(len(headers), 3)
        expected_headers = {
            b"Content-Length": str(len(test_file_contents)).encode("ascii"),
            b"Content-Type": b"text/x-python",
            b"Content-Disposition": b'inline; filename="urls.py"',
        }
        for key, value in headers:
            try:
                self.assertEqual(value, expected_headers[key])
            except AssertionError:
                # Windows registry may not be configured with correct
                # mimetypes.
                if sys.platform == "win32" and key == b"Content-Type":
                    self.assertEqual(value, b"text/plain")
                else:
                    raise

        # Warning ignored here.
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], test_file_contents)
        # Allow response.close() to finish.
        await communicator.wait()