def test_fileuploads_closed_at_request_end(self):
        file = tempfile.NamedTemporaryFile
        with file() as f1, file() as f2a, file() as f2b:
            response = self.client.post(
                "/fd_closing/t/",
                {
                    "file": f1,
                    "file2": (f2a, f2b),
                },
            )

        request = response.wsgi_request
        # The files were parsed.
        self.assertTrue(hasattr(request, "_files"))

        file = request._files["file"]
        self.assertTrue(file.closed)

        files = request._files.getlist("file2")
        self.assertTrue(files[0].closed)
        self.assertTrue(files[1].closed)