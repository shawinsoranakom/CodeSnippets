async def test_static_file_response(self):
        application = ASGIStaticFilesHandler(get_asgi_application())
        # Construct HTTP request.
        scope = self.async_request_factory._base_scope(path="/static/file.txt")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        # Get the file content.
        file_path = TEST_STATIC_ROOT / "file.txt"
        with open(file_path, "rb") as test_file:
            test_file_contents = test_file.read()
        # Read the response.
        stat = file_path.stat()
        response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        self.assertEqual(
            set(response_start["headers"]),
            {
                (b"Content-Length", str(len(test_file_contents)).encode("ascii")),
                (b"Content-Type", b"text/plain"),
                (b"Content-Disposition", b'inline; filename="file.txt"'),
                (b"Last-Modified", http_date(stat.st_mtime).encode("ascii")),
            },
        )
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], test_file_contents)
        # Allow response.close() to finish.
        await communicator.wait()